import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import { atualizarStatusPedido, criarPedido, getConta, listPedidos, listProdutos } from "../../api/endpoints";
import ChamadosBanner from "../../components/ChamadosBanner";
import Conexao from "../../components/Conexao";
import type { Conta, Pedido, PedidoStatus, Produto } from "../../types/domain";
import { NOME_STATUS_PEDIDO, formatarReais } from "../../utils/formatar";
import { useWebSocket, wsUrlParaStaff } from "../../ws/useWebSocket";

interface ItemCarrinho {
  produto: Produto;
  quantidade: number;
  observacao: string;
}

export default function ComandaDetalhe() {
  const { comandaId } = useParams<{ comandaId: string }>();
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [conta, setConta] = useState<Conta | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const [produtoId, setProdutoId] = useState("");
  const [quantidade, setQuantidade] = useState("1");
  const [observacao, setObservacao] = useState("");
  const [carrinho, setCarrinho] = useState<ItemCarrinho[]>([]);
  const [enviando, setEnviando] = useState(false);

  const carregar = useCallback(async () => {
    if (!comandaId) return;
    try {
      const [listaPedidos, contaAtual] = await Promise.all([listPedidos({ comandaId }), getConta(comandaId, false)]);
      setPedidos(listaPedidos);
      setConta(contaAtual);
      setErro(null);
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao carregar pedidos");
    }
  }, [comandaId]);

  useEffect(() => {
    listProdutos()
      .then((lista) => {
        const disponiveis = lista.filter((p) => p.disponivel);
        setProdutos(disponiveis);
        if (disponiveis.length > 0) setProdutoId(disponiveis[0].id);
      })
      .catch((err) => setErro(err instanceof ApiError ? err.message : "Erro ao carregar cardápio"));
    carregar();
  }, [carregar]);

  const conectado = useWebSocket(
    wsUrlParaStaff(),
    (evento) => {
      if (evento.tipo.startsWith("pedido_") && evento.comanda_id === comandaId) carregar();
    },
    carregar,
  );

  // Cardápio agrupado por categoria, para o <select> com <optgroup>.
  const categorias = useMemo(() => {
    const grupos = new Map<string, Produto[]>();
    for (const produto of produtos) {
      grupos.set(produto.categoria, [...(grupos.get(produto.categoria) ?? []), produto]);
    }
    return [...grupos.entries()];
  }, [produtos]);

  function handleAdicionar(event: React.FormEvent) {
    event.preventDefault();
    const produto = produtos.find((p) => p.id === produtoId);
    const qtd = Number(quantidade);
    if (!produto || !Number.isInteger(qtd) || qtd < 1) return;
    setCarrinho([...carrinho, { produto, quantidade: qtd, observacao: observacao.trim() }]);
    setQuantidade("1");
    setObservacao("");
  }

  function handleRemover(indice: number) {
    setCarrinho(carrinho.filter((_, i) => i !== indice));
  }

  async function handleLancar() {
    if (!comandaId || carrinho.length === 0) return;
    setEnviando(true);
    try {
      await criarPedido(
        comandaId,
        carrinho.map((item) => ({
          produto_id: item.produto.id,
          quantidade: item.quantidade,
          observacao: item.observacao || undefined,
        })),
      );
      setCarrinho([]);
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao lançar pedido");
    } finally {
      setEnviando(false);
    }
  }

  async function handleMudarStatus(pedido: Pedido, novoStatus: PedidoStatus) {
    if (novoStatus === "cancelado" && !confirm(`Cancelar o pedido da mesa ${pedido.mesa_numero}?`)) return;
    try {
      await atualizarStatusPedido(pedido.id, novoStatus);
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao atualizar pedido");
    }
  }

  const totalCarrinho = carrinho.reduce((soma, item) => soma + Number(item.produto.preco) * item.quantidade, 0);

  return (
    <main className="pagina">
      <ChamadosBanner />
      <div className="linha-entre" style={{ marginTop: 8 }}>
        <Link to="/salao/mesas">← voltar</Link>
        <Conexao conectado={conectado} />
      </div>
      <h1>Comanda{conta ? ` — Mesa ${conta.mesa_numero}` : ""}</h1>
      {conta && (
        <p style={{ fontSize: 18 }}>
          Consumo até agora: <strong>{formatarReais(conta.subtotal)}</strong>
        </p>
      )}

      <h2>Novo pedido</h2>
      <form onSubmit={handleAdicionar} style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        <select value={produtoId} onChange={(e) => setProdutoId(e.target.value)}>
          {categorias.map(([categoria, lista]) => (
            <optgroup key={categoria} label={categoria}>
              {lista.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nome} — {formatarReais(p.preco)}
                </option>
              ))}
            </optgroup>
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
        <button type="submit" disabled={produtos.length === 0}>
          Adicionar
        </button>
      </form>

      {carrinho.length > 0 && (
        <div className="cartao" style={{ borderStyle: "dashed", marginBottom: 24 }}>
          <ul style={{ margin: 0, paddingLeft: 16 }}>
            {carrinho.map((item, indice) => (
              <li key={indice} style={{ marginBottom: 4 }}>
                {item.quantidade}x {item.produto.nome}
                {item.observacao ? ` (${item.observacao})` : ""} —{" "}
                {formatarReais(Number(item.produto.preco) * item.quantidade)}{" "}
                <button type="button" className="perigo" onClick={() => handleRemover(indice)}>
                  remover
                </button>
              </li>
            ))}
          </ul>
          <div className="linha-entre" style={{ marginTop: 8 }}>
            <strong>{formatarReais(totalCarrinho)}</strong>
            <button className="primario" onClick={handleLancar} disabled={enviando}>
              {enviando ? "Lançando..." : `Lançar pedido (${carrinho.length} ${carrinho.length === 1 ? "item" : "itens"})`}
            </button>
          </div>
        </div>
      )}

      {erro && <p className="erro">{erro}</p>}

      <h2>Pedidos</h2>
      {pedidos.length === 0 && <p>Nenhum pedido ainda.</p>}
      {pedidos.map((pedido) => (
        <div
          key={pedido.id}
          className={`cartao${pedido.status === "pronto" ? " pronto" : pedido.status === "cancelado" ? " apagado" : ""}`}
          style={{ marginBottom: 8 }}
        >
          <div className="linha-entre">
            <strong>{NOME_STATUS_PEDIDO[pedido.status]}</strong>
            <span>
              {pedido.status === "pronto" && (
                <button className="primario" onClick={() => handleMudarStatus(pedido, "entregue")}>
                  Marcar entregue
                </button>
              )}
              {pedido.status === "recebido" && (
                <button className="perigo" onClick={() => handleMudarStatus(pedido, "cancelado")}>
                  Cancelar
                </button>
              )}
            </span>
          </div>
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
