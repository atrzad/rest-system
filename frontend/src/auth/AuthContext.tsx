import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";

import { login as loginRequest } from "../api/endpoints";
import type { AuthUser } from "../types/auth";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, senha: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const STORAGE_KEY = "rest-system:auth";

function loadStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setUser(loadStoredUser());
    setLoading(false);
  }, []);

  async function login(email: string, senha: string) {
    const resposta = await loginRequest(email, senha);
    const authUser: AuthUser = { nome: resposta.nome, role: resposta.role, token: resposta.access_token };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(authUser));
    localStorage.setItem("token", authUser.token);
    setUser(authUser);
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem("token");
    setUser(null);
  }

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth precisa estar dentro de um AuthProvider");
  return ctx;
}
