import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { Role } from "../types/auth";
import { useTitulo } from "../utils/useTitulo";

// Cada perfil cai direto na tela de trabalho.
const HOME_POR_ROLE: Record<Role, string> = {
  admin: "/admin/dashboard",
  salao: "/salao/mesas",
  cozinha: "/cozinha/kds",
};

export default function Login() {
  const { user, aviso, login } = useAuth();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  useTitulo("Entrar");

  if (user) {
    return <Navigate to={HOME_POR_ROLE[user.role]} replace />;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await login(email, senha);
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Não foi possível entrar. Tente novamente.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="pagina" style={{ maxWidth: 380, marginTop: "10vh" }}>
      <h1>Rest System</h1>
      {aviso && !erro && (
        <div className="alerta-caixa atencao" role="status">
          {aviso}
        </div>
      )}
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--e-4)" }}>
        <label className="campo">
          <span>E-mail</span>
          <input
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="campo">
          <span>Senha</span>
          <input
            type="password"
            autoComplete="current-password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
          />
        </label>
        {erro && (
          <p className="erro" role="alert" style={{ margin: 0 }}>
            {erro}
          </p>
        )}
        <button type="submit" className="primario" disabled={enviando}>
          {enviando ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </main>
  );
}
