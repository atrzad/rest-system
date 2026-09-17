import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../../api/client";
import { atualizarStatusPedido, listPedidos } from "../../api/endpoints";
import { useAuth } from "../../auth/AuthContext";
import type { Pedido, PedidoStatus } from "../../types/domain";
import { useWebSocket, wsUrlParaStaff } from "../../ws/useWebSocket";

const COLUNAS: { status: PedidoStatus; titulo: string; proximo: PedidoStatus | null }[] = [
  { status: "recebido", titulo: "Recebido", proximo: "em_preparo" },
  { status: "em_preparo", titulo: "Em preparo", proximo: "pronto" },
  { status: "pronto", titulo: "Pronto", proximo: null },
];

export default function KDS() {
  const { user, logout } = useAuth();
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [erro, setErro] = useState<string | null>(null);

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
  }, [carregar]);

  useWebSocket(wsUrlParaStaff(), (evento) => {
    if (evento.tipo.startsWith("pedido_")) {
      carregar();
    }
  });

  async function avancarStatus(pedido: Pedido, novoStatus: PedidoStatus) {
    try {
      await atualizarStatusPedido(pedido.id, novoStatus);
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao atualizar status");
    }
  }

  return (
    <main style={{ maxWidth: 1000, margin: "3vh auto", fontFamily: "sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>KDS — Cozinha</h1>
        <div>
          <span style={{ marginRight: 12 }}>{user?.nome}</span>
          <button onClick={logout}>Sair</button>
        </div>
      </div>

      {erro && <p style={{ color: "crimson" }}>{erro}</p>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginTop: 16 }}>
        {COLUNAS.map((coluna) => (
          <div key={coluna.status} style={{ background: "#f4f4f4", borderRadius: 8, padding: 12 }}>
            <h2 style={{ fontSize: 16 }}>{coluna.titulo}</h2>
            {pedidos
              .filter((p) => p.status === coluna.status)
              .map((pedido) => (
                <div
                  key={pedido.id}
                  style={{ background: "#fff", border: "1px solid #ddd", borderRadius: 6, padding: 8, marginTop: 8 }}
                >
                  <strong>Mesa {pedido.mesa_numero}</strong>
                  <ul style={{ margin: "4px 0", paddingLeft: 16 }}>
                    {pedido.itens.map((item) => (
                      <li key={item.id}>
                        {item.quantidade}x {item.produto_nome}
                        {item.observacao ? ` (${item.observacao})` : ""}
                      </li>
                    ))}
                  </ul>
                  {coluna.proximo && (
                    <button onClick={() => avancarStatus(pedido, coluna.proximo as PedidoStatus)}>
                      {coluna.proximo === "em_preparo" ? "Iniciar preparo" : "Marcar como pronto"}
                    </button>
                  )}
                </div>
              ))}
          </div>
        ))}
      </div>
    </main>
  );
}
