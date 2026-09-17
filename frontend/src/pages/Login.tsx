import { FormEvent, useState } from "react";

export default function Login() {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    // Login real (chamada à API + JWT) entra na Etapa 1.
    console.log("login (placeholder)", { email });
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
        <button type="submit">Entrar</button>
      </form>
    </main>
  );
}
