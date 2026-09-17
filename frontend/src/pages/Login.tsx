import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { Role } from "../types/auth";

const HOME_POR_ROLE: Record<Role, string> = {
  admin: "/admin",
  salao: "/salao",
  cozinha: "/cozinha",
};

export default function Login() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

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
    <main style={{ maxWidth: 320, margin: "10vh auto", fontFamily: "sans-serif" }}>
      <h1>Rest System</h1>
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <label>
          E-mail
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: "100%" }}
          />
        </label>
        <label>
          Senha
          <input
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
            style={{ width: "100%" }}
          />
        </label>
        {erro && <p style={{ color: "crimson" }}>{erro}</p>}
        <button type="submit" disabled={enviando}>
          {enviando ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </main>
  );
}
