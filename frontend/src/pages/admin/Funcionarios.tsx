import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import { atualizarFuncionario, criarFuncionario, listFuncionarios } from "../../api/endpoints";
import type { Funcionario, Role } from "../../types/auth";

const ROLES: Role[] = ["admin", "salao", "cozinha"];

export default function Funcionarios() {
  const [funcionarios, setFuncionarios] = useState<Funcionario[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [role, setRole] = useState<Role>("salao");
  const [criando, setCriando] = useState(false);

  async function carregar() {
    setCarregando(true);
    try {
      setFuncionarios(await listFuncionarios());
      setErro(null);
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao carregar funcionários");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    carregar();
  }, []);

  async function handleCriar(event: FormEvent) {
    event.preventDefault();
    setCriando(true);
    setErro(null);
    try {
      await criarFuncionario({ nome, email, senha, role });
      setNome("");
      setEmail("");
      setSenha("");
      setRole("salao");
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao criar funcionário");
    } finally {
      setCriando(false);
    }
  }

  async function handleAlterarRole(f: Funcionario, novaRole: Role) {
    try {
      await atualizarFuncionario(f.id, { role: novaRole });
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao alterar role");
    }
  }

  async function handleAlterarAtivo(f: Funcionario, ativo: boolean) {
    try {
      await atualizarFuncionario(f.id, { ativo });
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao alterar status");
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: "5vh auto", fontFamily: "sans-serif" }}>
      <p>
        <Link to="/admin">← voltar</Link>
      </p>
      <h1>Funcionários</h1>

      <form onSubmit={handleCriar} style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 24 }}>
        <input placeholder="Nome" value={nome} onChange={(e) => setNome(e.target.value)} required />
        <input
          type="email"
          placeholder="E-mail"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Senha"
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
          required
        />
        <select value={role} onChange={(e) => setRole(e.target.value as Role)}>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <button type="submit" disabled={criando}>
          {criando ? "Criando..." : "Adicionar"}
        </button>
      </form>

      {erro && <p style={{ color: "crimson" }}>{erro}</p>}

      {carregando ? (
        <p>Carregando...</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
              <th>Nome</th>
              <th>E-mail</th>
              <th>Role</th>
              <th>Ativo</th>
            </tr>
          </thead>
          <tbody>
            {funcionarios.map((f) => (
              <tr key={f.id} style={{ borderBottom: "1px solid #eee" }}>
                <td>{f.nome}</td>
                <td>{f.email}</td>
                <td>
                  <select value={f.role} onChange={(e) => handleAlterarRole(f, e.target.value as Role)}>
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    type="checkbox"
                    checked={f.ativo}
                    onChange={(e) => handleAlterarAtivo(f, e.target.checked)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
