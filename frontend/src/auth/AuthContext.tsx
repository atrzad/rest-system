import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";

import { login as loginRequest } from "../api/endpoints";
import type { AuthUser } from "../types/auth";
import { EVENTO_SESSAO_EXPIRADA, expiracaoDoToken } from "./sessao";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  /** Mensagem para a tela de login (ex.: "Sua sessão expirou"). */
  aviso: string | null;
  login: (email: string, senha: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const STORAGE_KEY = "rest-system:auth";
const AVISO_EXPIRADA = "Sua sessão expirou. Entre de novo para continuar.";

function limparSessao() {
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem("token");
}

function tokenVencido(token: string): boolean {
  const expira = expiracaoDoToken(token);
  return expira !== null && expira <= Date.now();
}

/** Usuário salvo no aparelho, ou null se não houver ou se o token já tiver vencido. */
function carregarSessao(): { user: AuthUser | null; aviso: string | null } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const user = raw ? (JSON.parse(raw) as AuthUser) : null;
    if (user && tokenVencido(user.token)) {
      limparSessao();
      return { user: null, aviso: AVISO_EXPIRADA };
    }
    return { user, aviso: null };
  } catch {
    return { user: null, aviso: null };
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [inicial] = useState(carregarSessao);
  const [user, setUser] = useState<AuthUser | null>(inicial.user);
  const [aviso, setAviso] = useState<string | null>(inicial.aviso);

  const expirar = useCallback(() => {
    limparSessao();
    setUser(null);
    setAviso(AVISO_EXPIRADA);
  }, []);

  // A API respondeu 401 em alguma tela.
  useEffect(() => {
    window.addEventListener(EVENTO_SESSAO_EXPIRADA, expirar);
    return () => window.removeEventListener(EVENTO_SESSAO_EXPIRADA, expirar);
  }, [expirar]);

  // Tela parada (ex.: KDS ligado a noite toda): sai sozinho na hora em que o token vence.
  useEffect(() => {
    if (!user) return;
    const expira = expiracaoDoToken(user.token);
    if (expira === null) return;
    const espera = Math.min(Math.max(expira - Date.now(), 0), 2 ** 31 - 1);
    const id = setTimeout(expirar, espera);
    return () => clearTimeout(id);
  }, [user, expirar]);

  async function login(email: string, senha: string) {
    const resposta = await loginRequest(email, senha);
    const authUser: AuthUser = { nome: resposta.nome, role: resposta.role, token: resposta.access_token };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(authUser));
    localStorage.setItem("token", authUser.token);
    setAviso(null);
    setUser(authUser);
  }

  function logout() {
    limparSessao();
    setAviso(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading: false, aviso, login, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth precisa estar dentro de um AuthProvider");
  return ctx;
}
