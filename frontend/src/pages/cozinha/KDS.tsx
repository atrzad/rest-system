import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../../api/client";
import { atualizarStatusPedido, listPedidos } from "../../api/endpoints";
import { useAuth } from "../../auth/AuthContext";
import Conexao from "../../components/Conexao";
import type { Pedido, PedidoStatus } from "../../types/domain";
import { tocarAlerta } from "../../utils/som";
import { tempoDesde } from "../../utils/tempo";
import { useWebSocket, wsUrlParaStaff } from "../../ws/useWebSocket";

const COLUNAS: { status: PedidoStatus; titulo: string; proximo: PedidoStatus | null }[] = [
  { status: "recebido", titulo: "Recebido", proximo: "em_preparo" },
  { status: "em_preparo", titulo: "Em preparo", proximo: "pronto" },
  { status: "pronto", titulo: "Pronto", proximo: null },
];

// Minutos desde que o pedido chegou a partir dos quais o cartão fica amarelo / vermelho.
const MINUTOS_ATENCAO = 10;
const MINUTOS_ATRASADO = 20;

function corDoAtraso(pedido: Pedido, agora: number): string {
  const minutos = (agora - new Date(pedido.criado_em).getTime()) / 60000;
  if (minutos >= MINUTOS_ATRASADO) return "var(--perigo)";
  if (minutos >= MINUTOS_ATENCAO) return "var(--alerta)";
  return "var(--borda)";
}

export default function KDS() {
  const { user, logout } = useAuth();
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [agora, setAgora] = useState(() => Date.now());

  const carregar = useCallback(async () => {
    try {
      const [recebidos, emPreparo, prontos] = await Promise.all([
        listPedidos({ status: "recebido" }),
        listPedidos({ status: "em_preparo" }),
        listPedidos({ status: "pronto" }),
      ]);
      setPedidos([...recebidos, ...emPreparo, ...prontos]);
      setErro(null);
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao carregar pedidos");
    }
  }, []);

  useEffect(() => {
    carregar();
    // Relógio a cada 30s para o tempo e a cor de atraso andarem sozinhos.
    const intervalo = setInterval(() => setAgora(Date.now()), 30000);
    return () => clearInterval(intervalo);
  }, [carregar]);

  const conectado = useWebSocket(
    wsUrlParaStaff(),
    (evento) => {
      if (evento.tipo === "pedido_criado") tocarAlerta();
      if (evento.tipo.startsWith("pedido_")) carregar();
    },
    carregar,
  );

  async function avancarStatus(pedido: Pedido, novoStatus: PedidoStatus) {
    if (novoStatus === "cancelado" && !confirm(`Cancelar o pedido da mesa ${pedido.mesa_numero}?`)) return;
    try {
      await atualizarStatusPedido(pedido.id, novoStatus);
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao atualizar status");
    }
  }

  return (
    <main className="pagina-larga" style={{ fontSize: 18 }}>
      <div className="linha-entre">
        <h1 style={{ margin: 0 }}>KDS — Cozinha</h1>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <Conexao conectado={conectado} />
          <span>{user?.nome}</span>
          <button onClick={logout}>Sair</button>
        </div>
      </div>

      {erro && <p className="erro">{erro}</p>}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: 16,
          marginTop: 16,
        }}
      >
        {COLUNAS.map((coluna) => {
          const daColuna = pedidos.filter((p) => p.status === coluna.status);
          return (
            <section key={coluna.status} className="cartao" style={{ padding: 12 }}>
              <h2 style={{ margin: "0 0 8px" }}>
                {coluna.titulo} <span className="texto-2">({daColuna.length})</span>
              </h2>
              {daColuna.map((pedido) => (
                <div
                  key={pedido.id}
                  style={{
                    background: "var(--fundo)",
                    border: "1px solid var(--borda)",
                    borderLeft: `6px solid ${coluna.status === "pronto" ? "var(--ok)" : corDoAtraso(pedido, agora)}`,
                    borderRadius: 6,
                    padding: 10,
                    marginTop: 8,
                  }}
                >
                  <div className="linha-entre">
                    <strong style={{ fontSize: 22 }}>Mesa {pedido.mesa_numero}</strong>
                    <span className="texto-2">{tempoDesde(pedido.criado_em, agora)}</span>
                  </div>
                  <ul style={{ margin: "6px 0", paddingLeft: 20 }}>
                    {pedido.itens.map((item) => (
                      <li key={item.id}>
                        <strong>{item.quantidade}x</strong> {item.produto_nome}
                        {item.observacao && <div className="aviso">↳ {item.observacao}</div>}
                      </li>
                    ))}
                  </ul>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {coluna.proximo && (
                      <button className="primario" onClick={() => avancarStatus(pedido, coluna.proximo as PedidoStatus)}>
                        {coluna.proximo === "em_preparo" ? "Iniciar preparo" : "Marcar como pronto"}
                      </button>
                    )}
                    {coluna.status !== "pronto" && (
                      <button className="perigo" onClick={() => avancarStatus(pedido, "cancelado")}>
                        Cancelar
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </section>
          );
        })}
      </div>
    </main>
  );
}
