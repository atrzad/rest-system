import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { QRCodeSVG } from "qrcode.react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import { criarMesa, listMesas, regenerarTokenMesa } from "../../api/endpoints";
import type { Mesa } from "../../types/domain";

export default function Mesas() {
  const [mesas, setMesas] = useState<Mesa[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const [numero, setNumero] = useState("");
  const [capacidade, setCapacidade] = useState("");
  const [criando, setCriando] = useState(false);
  const [qrAberto, setQrAberto] = useState<string | null>(null);

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

  async function handleRegenerar(mesa: Mesa) {
    const ok = confirm(
      `Gerar um código novo para a mesa ${mesa.numero}? O QR impresso atual para de funcionar e precisa ser reimpresso.`,
    );
    if (!ok) return;
    try {
      await regenerarTokenMesa(mesa.id);
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao gerar novo código");
    }
  }

  return (
    <main className="pagina">
      <p>
        <Link to="/admin">← voltar</Link>
      </p>
      <h1>Mesas</h1>
      <p>
        <Link to="/admin/mesas/imprimir">Imprimir QR codes de todas as mesas</Link>
      </p>

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

      {erro && <p className="erro">{erro}</p>}

      {carregando ? (
        <p>Carregando...</p>
      ) : (
        <ul style={{ textAlign: "left" }}>
          {mesas.map((m) => (
            <li key={m.id} style={{ marginBottom: 8 }}>
              Mesa {m.numero} {m.capacidade ? `— ${m.capacidade} lugares` : ""} {m.ativa ? "" : "(inativa)"}
              <br />
              <small>
                Código: <code>{m.token}</code>{" "}
                <button onClick={() => setQrAberto(qrAberto === m.id ? null : m.id)}>
                  {qrAberto === m.id ? "Esconder QR" : "QR"}
                </button>{" "}
                <button onClick={() => handleRegenerar(m)}>Gerar novo código</button>
              </small>
              {qrAberto === m.id && m.url_qr && (
                <div style={{ marginTop: 8 }}>
                  <QRCodeSVG value={m.url_qr} size={180} marginSize={2} />
                  <br />
                  <a href={m.url_qr} target="_blank" rel="noreferrer">
                    <small>{m.url_qr}</small>
                  </a>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
