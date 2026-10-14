import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { atenderChamado, listChamados } from "../api/endpoints";
import type { Chamado } from "../types/domain";
import { tocarAlerta } from "../utils/som";
import { tempoDesde } from "../utils/tempo";
import { useWebSocket, wsUrlParaStaff } from "../ws/useWebSocket";

/** Faixa fixa no topo das telas do salão com as mesas que chamaram o garçom. */
export default function ChamadosBanner() {
  const [chamados, setChamados] = useState<Chamado[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [, setRelogio] = useState(0);

  const carregar = useCallback(async () => {
    try {
      setChamados(await listChamados());
      setErro(null);
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao carregar chamados");
    }
  }, []);

  useEffect(() => {
    carregar();
    // Re-renderiza a cada 30s para o "há N min" andar sozinho.
    const intervalo = setInterval(() => setRelogio((n) => n + 1), 30000);
    return () => clearInterval(intervalo);
  }, [carregar]);

  useWebSocket(wsUrlParaStaff(), (evento) => {
    if (evento.tipo === "garcom_chamado") {
      tocarAlerta();
      carregar();
    } else if (evento.tipo === "chamado_atendido") {
      carregar();
    }
  });

  async function handleAtender(chamado: Chamado) {
    try {
      await atenderChamado(chamado.id);
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao atender chamado");
    }
  }

  if (chamados.length === 0 && !erro) return null;

  return (
    <div
      role="alert"
      style={{
        position: "sticky",
        top: 0,
        zIndex: 10,
        background: "#fde68a",
        color: "#3b2f00",
        padding: "8px 12px",
        display: "flex",
        flexWrap: "wrap",
        gap: 8,
        alignItems: "center",
        fontFamily: "sans-serif",
      }}
    >
      {erro && <span style={{ color: "crimson" }}>{erro}</span>}
      {chamados.map((chamado) => (
        <span
          key={chamado.id}
          style={{ background: "#fff8dc", borderRadius: 6, padding: "4px 8px", display: "inline-flex", gap: 8 }}
        >
          <strong>Mesa {chamado.mesa_numero} chamou</strong>
          <span>{tempoDesde(chamado.criado_em)}</span>
          <button onClick={() => handleAtender(chamado)}>Atender</button>
        </span>
      ))}
    </div>
  );
}
