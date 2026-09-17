import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import { abrirComandaPorMesa, fecharComanda, listComandas, listMesas } from "../../api/endpoints";
import type { Comanda, Mesa } from "../../types/domain";
import { useWebSocket, wsUrlParaStaff } from "../../ws/useWebSocket";

export default function Mesas() {
  const [mesas, setMesas] = useState<Mesa[]>([]);
  const [comandasAbertas, setComandasAbertas] = useState<Comanda[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [acaoEmAndamento, setAcaoEmAndamento] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const [listaMesas, listaComandas] = await Promise.all([listMesas(), listComandas("aberta")]);
      setMesas(listaMesas);
      setComandasAbertas(listaComandas);
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
      await abrirComandaPorMesa(mesa.numero, "garcom");
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao abrir comanda");
    } finally {
      setAcaoEmAndamento(null);
    }
  }

  async function handleFechar(comanda: Comanda) {
    setAcaoEmAndamento(comanda.id);
    try {
      await fecharComanda(comanda.id);
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao fechar comanda");
    } finally {
      setAcaoEmAndamento(null);
    }
  }

  return (
    <main style={{ maxWidth: 640, margin: "5vh auto", fontFamily: "sans-serif" }}>
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
                {comanda ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <Link to={`/salao/comandas/${comanda.id}`}>Ver comanda</Link>
                    <button disabled={emAndamento} onClick={() => handleFechar(comanda)}>
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
    </main>
  );
}
