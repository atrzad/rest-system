import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import { criarPedido, listPedidos, listProdutos } from "../../api/endpoints";
import type { Pedido, Produto } from "../../types/domain";
import { useWebSocket, wsUrlParaStaff } from "../../ws/useWebSocket";

export default function ComandaDetalhe() {
  const { comandaId } = useParams<{ comandaId: string }>();
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [erro, setErro] = useState<string | null>(null);

  const [produtoId, setProdutoId] = useState("");
  const [quantidade, setQuantidade] = useState("1");
  const [observacao, setObservacao] = useState("");
  const [enviando, setEnviando] = useState(false);

  const carregar = useCallback(async () => {
    if (!comandaId) return;
    try {
      setPedidos(await listPedidos({ comandaId }));
      setErro(null);
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao carregar pedidos");
    }
  }, [comandaId]);

  useEffect(() => {
    listProdutos()
      .then((lista) => {
        setProdutos(lista.filter((p) => p.disponivel));
        if (lista.length > 0) setProdutoId(lista[0].id);
      })
      .catch((err) => setErro(err instanceof ApiError ? err.message : "Erro ao carregar cardápio"));
    carregar();
  }, [carregar]);

  useWebSocket(wsUrlParaStaff(), (evento) => {
    if (evento.tipo.startsWith("pedido_") && evento.comanda_id === comandaId) {
      carregar();
    }
  });

  async function handleLancar(event: React.FormEvent) {
    event.preventDefault();
    if (!comandaId || !produtoId) return;
    setEnviando(true);
    try {
      await criarPedido(comandaId, [
        { produto_id: produtoId, quantidade: Number(quantidade), observacao: observacao || undefined },
      ]);
      setQuantidade("1");
      setObservacao("");
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao lançar pedido");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main style={{ maxWidth: 640, margin: "5vh auto", fontFamily: "sans-serif" }}>
      <p>
        <Link to="/salao/mesas">← voltar</Link>
      </p>
      <h1>Comanda</h1>

      <form onSubmit={handleLancar} style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 24 }}>
        <select value={produtoId} onChange={(e) => setProdutoId(e.target.value)}>
          {produtos.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nome} — R$ {p.preco}
            </option>
          ))}
        </select>
        <input
          type="number"
          min="1"
          value={quantidade}
          onChange={(e) => setQuantidade(e.target.value)}
          style={{ width: 60 }}
        />
        <input
          placeholder="Observação (opcional)"
          value={observacao}
          onChange={(e) => setObservacao(e.target.value)}
        />
        <button type="submit" disabled={enviando || produtos.length === 0}>
          {enviando ? "Lançando..." : "Lançar pedido"}
        </button>
      </form>

      {erro && <p style={{ color: "crimson" }}>{erro}</p>}

      <h2>Pedidos</h2>
      {pedidos.length === 0 && <p>Nenhum pedido ainda.</p>}
      {pedidos.map((pedido) => (
        <div key={pedido.id} style={{ border: "1px solid #ddd", borderRadius: 6, padding: 8, marginBottom: 8 }}>
          <strong>Status: {pedido.status}</strong>
          <ul>
            {pedido.itens.map((item) => (
              <li key={item.id}>
                {item.quantidade}x {item.produto_nome}
                {item.observacao ? ` (${item.observacao})` : ""}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </main>
  );
}
