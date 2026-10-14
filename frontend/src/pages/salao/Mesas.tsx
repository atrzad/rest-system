import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import { abrirComandaPorMesa, fecharComanda, getConta, listComandas, listMesas, listPedidos } from "../../api/endpoints";
import ChamadosBanner from "../../components/ChamadosBanner";
import type { Comanda, Conta, Mesa } from "../../types/domain";
import { formatarReais } from "../../utils/formatar";
import { useWebSocket, wsUrlParaStaff } from "../../ws/useWebSocket";

export default function Mesas() {
  const [mesas, setMesas] = useState<Mesa[]>([]);
  const [comandasAbertas, setComandasAbertas] = useState<Comanda[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [acaoEmAndamento, setAcaoEmAndamento] = useState<string | null>(null);
  const [prontosPorComanda, setProntosPorComanda] = useState<Record<string, number>>({});

  // Fechamento: comanda escolhida + prévia da conta (com ou sem taxa de serviço).
  const [fechando, setFechando] = useState<Comanda | null>(null);
  const [conta, setConta] = useState<Conta | null>(null);
  const [comTaxa, setComTaxa] = useState(true);
  const [erroFechamento, setErroFechamento] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const [listaMesas, listaComandas, prontos] = await Promise.all([
        listMesas(),
        listComandas("aberta"),
        listPedidos({ status: "pronto" }),
      ]);
      setMesas(listaMesas.filter((m) => m.ativa));
      setComandasAbertas(listaComandas);
      const contagem: Record<string, number> = {};
      for (const pedido of prontos) contagem[pedido.comanda_id] = (contagem[pedido.comanda_id] ?? 0) + 1;
      setProntosPorComanda(contagem);
      setErro(null);
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao carregar mesas");
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  useWebSocket(wsUrlParaStaff(), (evento) => {
    if (evento.tipo.startsWith("pedido_") || evento.tipo.startsWith("comanda_") || evento.tipo === "garcom_chamado") {
      carregar();
    }
  });

  function comandaDaMesa(mesa: Mesa): Comanda | undefined {
    return comandasAbertas.find((c) => c.mesa_id === mesa.id);
  }

  async function handleAbrir(mesa: Mesa) {
    setAcaoEmAndamento(mesa.id);
    try {
      await abrirComandaPorMesa(mesa.numero);
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao abrir comanda");
    } finally {
      setAcaoEmAndamento(null);
    }
  }

  // A prévia da conta é recarregada sempre que muda a comanda ou a opção de taxa.
  useEffect(() => {
    if (!fechando) return;
    let atual = true; // ignora respostas de uma prévia antiga se a taxa for alternada rápido
    getConta(fechando.id, comTaxa)
      .then((c) => {
        if (!atual) return;
        setConta(c);
        setErroFechamento(null);
      })
      .catch((err) => {
        if (atual) setErroFechamento(err instanceof ApiError ? err.message : "Erro ao calcular a conta");
      });
    return () => {
      atual = false;
    };
  }, [fechando, comTaxa]);

  function handleAbrirFechamento(comanda: Comanda) {
    setConta(null);
    setComTaxa(true);
    setErroFechamento(null);
    setFechando(comanda);
  }

  function handleCancelarFechamento() {
    setFechando(null);
    setConta(null);
  }

  async function handleConfirmarFechamento() {
    if (!fechando) return;
    setAcaoEmAndamento(fechando.id);
    try {
      await fecharComanda(fechando.id, comTaxa);
      handleCancelarFechamento();
      await carregar();
    } catch (err) {
      setErroFechamento(err instanceof ApiError ? err.message : "Erro ao fechar comanda");
    } finally {
      setAcaoEmAndamento(null);
    }
  }

  return (
    <main style={{ maxWidth: 640, margin: "5vh auto", fontFamily: "sans-serif" }}>
      <ChamadosBanner />
      <p>
        <Link to="/salao">← voltar</Link>
      </p>
      <h1>Mesas</h1>

      {erro && <p style={{ color: "crimson" }}>{erro}</p>}

      {carregando ? (
        <p>Carregando...</p>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 12 }}>
          {mesas.map((mesa) => {
            const comanda = comandaDaMesa(mesa);
            const emAndamento = acaoEmAndamento === mesa.id || acaoEmAndamento === comanda?.id;
            return (
              <div
                key={mesa.id}
                style={{
                  border: "1px solid #ccc",
                  borderRadius: 8,
                  padding: 12,
                  background: comanda ? "#fff7e6" : "#f4f4f4",
                }}
              >
                <strong>Mesa {mesa.numero}</strong>
                <p style={{ margin: "4px 0" }}>{comanda ? "Ocupada" : "Livre"}</p>
                {comanda && prontosPorComanda[comanda.id] ? (
                  <p style={{ margin: "4px 0", color: "#1a7f37", fontWeight: "bold" }}>
                    {prontosPorComanda[comanda.id]} pronto(s) para entregar
                  </p>
                ) : null}
                {comanda ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <Link to={`/salao/comandas/${comanda.id}`}>Ver comanda</Link>
                    <button disabled={emAndamento} onClick={() => handleAbrirFechamento(comanda)}>
                      Fechar comanda
                    </button>
                  </div>
                ) : (
                  <button disabled={emAndamento || !mesa.ativa} onClick={() => handleAbrir(mesa)}>
                    Abrir comanda
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {fechando && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 16,
          }}
        >
          <div style={{ background: "#fff", borderRadius: 8, padding: 16, width: "100%", maxWidth: 420 }}>
            <h2 style={{ marginTop: 0 }}>Fechar conta — Mesa {fechando.mesa_numero}</h2>
            {!conta && !erroFechamento && <p>Calculando...</p>}
            {conta && (
              <>
                {conta.itens.length === 0 ? (
                  <p>Nenhum item consumido.</p>
                ) : (
                  <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <tbody>
                      {conta.itens.map((item) => (
                        <tr key={`${item.produto_id}-${item.preco_unitario}`}>
                          <td>
                            {item.quantidade}x {item.produto_nome}
                          </td>
                          <td style={{ textAlign: "right" }}>{formatarReais(item.valor)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                <hr />
                <p style={{ display: "flex", justifyContent: "space-between", margin: "4px 0" }}>
                  <span>Subtotal</span>
                  <span>{formatarReais(conta.subtotal)}</span>
                </p>
                <label style={{ display: "flex", justifyContent: "space-between", margin: "4px 0" }}>
                  <span>
                    <input type="checkbox" checked={comTaxa} onChange={(e) => setComTaxa(e.target.checked)} /> Taxa
                    de serviço (10%)
                  </span>
                  <span>{formatarReais(conta.taxa_servico)}</span>
                </label>
                <p style={{ display: "flex", justifyContent: "space-between", fontSize: 20, margin: "8px 0" }}>
                  <strong>Total</strong>
                  <strong>{formatarReais(conta.total)}</strong>
                </p>
                {conta.pedidos_pendentes > 0 && (
                  <p style={{ color: "#b45309" }}>
                    Há {conta.pedidos_pendentes} pedido(s) ainda não entregue(s). Entregue ou cancele antes de fechar.
                  </p>
                )}
              </>
            )}
            {erroFechamento && <p style={{ color: "crimson" }}>{erroFechamento}</p>}
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 12 }}>
              <button onClick={handleCancelarFechamento}>Voltar</button>
              <button
                onClick={handleConfirmarFechamento}
                disabled={!conta || conta.pedidos_pendentes > 0 || acaoEmAndamento === fechando.id}
              >
                Confirmar fechamento
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
