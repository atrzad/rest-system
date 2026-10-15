import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import { abrirComandaPublica, chamarGarcom, getContaPublica, getMesaPublica } from "../../api/endpoints";
import type { Conta, MesaPublica, ProdutoPublico } from "../../types/domain";
import { NOME_STATUS_PEDIDO, formatarReais } from "../../utils/formatar";
import { useTitulo } from "../../utils/useTitulo";
import { useWebSocket, wsUrlParaMesa } from "../../ws/useWebSocket";

const COR_STATUS: Record<string, string> = {
  recebido: "#6b7280",
  em_preparo: "#b45309",
  pronto: "#15803d",
  entregue: "#1d4ed8",
  cancelado: "#9ca3af",
};

/** Tela pública do cliente: /mesa/:numero?t=TOKEN (é para onde aponta o QR da mesa). */
export default function SelfView() {
  const { numero: numeroParam } = useParams<{ numero: string }>();
  const [searchParams] = useSearchParams();
  const numero = Number(numeroParam);
  const token = searchParams.get("t") ?? "";
  const origem = searchParams.get("origem") === "manual" ? "cliente_manual" : "cliente_qr";

  const [mesa, setMesa] = useState<MesaPublica | null>(null);
  const [conta, setConta] = useState<Conta | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [naoEncontrada, setNaoEncontrada] = useState(false);
  const [chamando, setChamando] = useState(false);
  useTitulo(Number.isInteger(numero) ? `Mesa ${numero}` : "Mesa");

  const carregar = useCallback(async () => {
    try {
      const dados = await getMesaPublica(numero, token);
      setMesa(dados);
      setConta(dados.comanda ? await getContaPublica(numero, token) : null);
      setErro(null);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404 && err.message === "Mesa não encontrada") {
        setNaoEncontrada(true);
      } else {
        setErro(err instanceof ApiError ? err.message : "Sem conexão. Tentando de novo...");
      }
    }
  }, [numero, token]);

  // Ao entrar pelo QR, abre a comanda da mesa (ou reaproveita a que já está aberta).
  useEffect(() => {
    if (!token || !Number.isInteger(numero)) {
      setNaoEncontrada(true);
      return;
    }
    abrirComandaPublica(numero, token, origem)
      .catch(() => undefined) // se falhar, carregar() mostra o erro certo
      .finally(carregar);
  }, [numero, token, origem, carregar]);

  useWebSocket(naoEncontrada ? null : wsUrlParaMesa(numero, token), () => {
    carregar();
  });

  const categorias = useMemo(() => {
    const grupos = new Map<string, ProdutoPublico[]>();
    for (const produto of mesa?.cardapio ?? []) {
      grupos.set(produto.categoria, [...(grupos.get(produto.categoria) ?? []), produto]);
    }
    return [...grupos.entries()];
  }, [mesa]);

  async function handleChamar() {
    setChamando(true);
    try {
      await chamarGarcom(numero, token);
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Não foi possível chamar o garçom");
    } finally {
      setChamando(false);
    }
  }

  if (naoEncontrada) {
    return (
      <main style={estiloPagina}>
        <h1>Mesa não encontrada</h1>
        <p>O código desta mesa não confere. Tente escanear o QR de novo ou digite o código impresso nele.</p>
        <Link to="/mesa">Digitar número e código</Link>
      </main>
    );
  }

  if (!mesa) {
    return (
      <main style={estiloPagina}>
        <p>{erro ?? "Carregando..."}</p>
      </main>
    );
  }

  const pedidosVisiveis = mesa.pedidos.filter((p) => p.status !== "cancelado");

  return (
    <main style={estiloPagina}>
      <h1 style={{ marginBottom: 4 }}>Mesa {mesa.numero}</h1>
      <p style={{ marginTop: 0 }}>Bem-vindo! Faça seu pedido com o garçom e acompanhe tudo por aqui.</p>

      <button
        onClick={handleChamar}
        disabled={chamando || mesa.chamado_aberto}
        style={{
          width: "100%",
          padding: "16px",
          fontSize: 20,
          borderRadius: 12,
          border: "none",
          color: "#fff",
          background: mesa.chamado_aberto ? "#15803d" : "#b45309", // fixos: texto branco legível nos dois temas
          cursor: mesa.chamado_aberto ? "default" : "pointer",
          opacity: 1, // desabilitado de propósito quando já chamou, mas a confirmação precisa ficar bem visível
        }}
      >
        {mesa.chamado_aberto ? "Garçom a caminho ✓" : chamando ? "Chamando..." : "Chamar garçom"}
      </button>

      {erro && <p className="erro">{erro}</p>}

      <section>
        <h2>Seus pedidos</h2>
        {pedidosVisiveis.length === 0 && <p>Nenhum pedido ainda.</p>}
        {pedidosVisiveis.map((pedido) => (
          <div key={pedido.id} style={estiloCartao}>
            <span
              style={{
                display: "inline-block",
                background: COR_STATUS[pedido.status],
                color: "#fff",
                borderRadius: 999,
                padding: "2px 10px",
                fontSize: 14,
              }}
            >
              {NOME_STATUS_PEDIDO[pedido.status]}
            </span>
            <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
              {pedido.itens.map((item) => (
                <li key={item.id}>
                  {item.quantidade}x {item.produto_nome}
                  {item.observacao ? ` (${item.observacao})` : ""}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      {conta && conta.itens.length > 0 && (
        <section>
          <h2>Sua conta</h2>
          <div style={estiloCartao}>
            <Linha rotulo="Consumo" valor={formatarReais(conta.subtotal)} />
            <Linha rotulo="Serviço (10%)" valor={formatarReais(conta.taxa_servico)} />
            <Linha rotulo={<strong>Total</strong>} valor={<strong>{formatarReais(conta.total)}</strong>} />
          </div>
        </section>
      )}

      <section>
        <h2>Cardápio</h2>
        {categorias.map(([categoria, produtos]) => (
          <div key={categoria}>
            <h3 style={{ marginBottom: 4 }}>{categoria}</h3>
            {produtos.map((produto) => (
              <Linha key={produto.id} rotulo={produto.nome} valor={formatarReais(produto.preco)} />
            ))}
          </div>
        ))}
      </section>
    </main>
  );
}

function Linha({ rotulo, valor }: { rotulo: React.ReactNode; valor: React.ReactNode }) {
  return (
    <p style={{ display: "flex", justifyContent: "space-between", gap: 12, margin: "4px 0" }}>
      <span>{rotulo}</span>
      <span>{valor}</span>
    </p>
  );
}

const estiloPagina: React.CSSProperties = { maxWidth: 480, margin: "0 auto", padding: 16 };

const estiloCartao: React.CSSProperties = {
  border: "1px solid var(--borda)",
  background: "var(--superficie)",
  borderRadius: 8,
  padding: 10,
  marginBottom: 8,
};
