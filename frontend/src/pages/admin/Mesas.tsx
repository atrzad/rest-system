import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import { criarMesa, listMesas } from "../../api/endpoints";
import type { Mesa } from "../../types/domain";

export default function Mesas() {
  const [mesas, setMesas] = useState<Mesa[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const [numero, setNumero] = useState("");
  const [capacidade, setCapacidade] = useState("");
  const [criando, setCriando] = useState(false);

  async function carregar() {
    setCarregando(true);
    try {
      setMesas(await listMesas());
      setErro(null);
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao carregar mesas");
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
      await criarMesa({ numero: Number(numero), capacidade: capacidade ? Number(capacidade) : null });
      setNumero("");
      setCapacidade("");
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao criar mesa");
    } finally {
      setCriando(false);
    }
  }

  return (
    <main style={{ maxWidth: 480, margin: "5vh auto", fontFamily: "sans-serif" }}>
      <p>
        <Link to="/admin">← voltar</Link>
      </p>
      <h1>Mesas</h1>

      <form onSubmit={handleCriar} style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        <input
          placeholder="Número"
          type="number"
          min="1"
          value={numero}
          onChange={(e) => setNumero(e.target.value)}
          required
        />
        <input
          placeholder="Capacidade (opcional)"
          type="number"
          min="1"
          value={capacidade}
          onChange={(e) => setCapacidade(e.target.value)}
        />
        <button type="submit" disabled={criando}>
          {criando ? "Criando..." : "Adicionar"}
        </button>
      </form>

      {erro && <p style={{ color: "crimson" }}>{erro}</p>}

      {carregando ? (
        <p>Carregando...</p>
      ) : (
        <ul>
          {mesas.map((m) => (
            <li key={m.id}>
              Mesa {m.numero} {m.capacidade ? `— ${m.capacidade} lugares` : ""} {m.ativa ? "" : "(inativa)"}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
