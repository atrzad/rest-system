import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import { abrirComandaPorMesa, fecharComanda, getConta, listComandas, listMesas, listPedidos } from "../../api/endpoints";
import ChamadosBanner from "../../components/ChamadosBanner";
import Conexao from "../../components/Conexao";
import type { Comanda, Conta, Mesa } from "../../types/domain";
import { formatarReais } from "../../utils/formatar";
import { tocarAlerta } from "../../utils/som";
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

  const conectado = useWebSocket(
    wsUrlParaStaff(),
    (evento) => {
      if (evento.tipo === "pedido_pronto") tocarAlerta(1);
      if (evento.tipo.startsWith("pedido_") || evento.tipo.startsWith("comanda_")) carregar();
    },
    carregar,
  );

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
    <main className="pagina">
      <ChamadosBanner />
      <div className="linha-entre" style={{ marginTop: 8 }}>
        <Link to="/salao">← voltar</Link>
        <Conexao conectado={conectado} />
      </div>
      <h1>Mesas</h1>

      {erro && <p className="erro">{erro}</p>}

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
                className={`cartao${comanda ? (prontosPorComanda[comanda.id] ? " pronto" : " ocupada") : ""}`}
              >
                <strong style={{ fontSize: 18 }}>Mesa {mesa.numero}</strong>
                <p className="texto-2" style={{ margin: "4px 0" }}>
                  {comanda ? "Ocupada" : "Livre"}
                </p>
                {comanda && prontosPorComanda[comanda.id] ? (
                  <p className="sucesso" style={{ margin: "4px 0" }}>
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
                  <button className="primario" disabled={emAndamento || !mesa.ativa} onClick={() => handleAbrir(mesa)}>
                    Abrir comanda
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {fechando && (
        <div className="modal-fundo">
          <div className="modal" role="dialog" aria-modal="true" aria-label={`Fechar conta da mesa ${fechando.mesa_numero}`}>
            <h2 style={{ marginTop: 0 }}>Fechar conta — Mesa {fechando.mesa_numero}</h2>
            {!conta && !erroFechamento && <p>Calculando...</p>}
            {conta && (
              <>
                {conta.itens.length === 0 ? (
                  <p>Nenhum item consumido.</p>
                ) : (
                  <table style={{ width: "100%" }}>
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
                <p className="linha-entre" style={{ margin: "4px 0" }}>
                  <span>Subtotal</span>
                  <span>{formatarReais(conta.subtotal)}</span>
                </p>
                <label className="linha-entre" style={{ margin: "4px 0" }}>
                  <span>
                    <input type="checkbox" checked={comTaxa} onChange={(e) => setComTaxa(e.target.checked)} /> Taxa
                    de serviço (10%)
                  </span>
                  <span>{formatarReais(conta.taxa_servico)}</span>
                </label>
                <p className="linha-entre" style={{ fontSize: 20, margin: "8px 0" }}>
                  <strong>Total</strong>
                  <strong>{formatarReais(conta.total)}</strong>
                </p>
                {conta.pedidos_pendentes > 0 && (
                  <p className="aviso">
                    Há {conta.pedidos_pendentes} pedido(s) ainda não entregue(s). Entregue ou cancele antes de fechar.
                  </p>
                )}
              </>
            )}
            {erroFechamento && <p className="erro">{erroFechamento}</p>}
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 12 }}>
              <button onClick={handleCancelarFechamento}>Voltar</button>
              <button
                className="primario"
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
