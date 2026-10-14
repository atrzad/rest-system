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
        background: "var(--chamado-fundo)",
        color: "var(--chamado-texto)",
        padding: "8px 12px",
        display: "flex",
        flexWrap: "wrap",
        gap: 8,
        alignItems: "center",
        borderRadius: 8,
        marginTop: 8,
      }}
    >
      {erro && <span className="erro">{erro}</span>}
      {chamados.map((chamado) => (
        <span
          key={chamado.id}
          style={{ display: "inline-flex", alignItems: "center", gap: 8 }}
        >
          <strong>Mesa {chamado.mesa_numero} chamou</strong>
          <span>{tempoDesde(chamado.criado_em)}</span>
          <button className="primario" onClick={() => handleAtender(chamado)}>
            Atender
          </button>
        </span>
      ))}
    </div>
  );
}
