import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ApiError } from "../../api/client";
import { getDashboardVendas } from "../../api/endpoints";
import type { DashboardVendas } from "../../types/domain";
import { formatarReais } from "../../utils/formatar";
import { useWebSocket, wsUrlParaStaff } from "../../ws/useWebSocket";

const PERIODOS = [
  { dias: 1, rotulo: "Hoje" },
  { dias: 7, rotulo: "7 dias" },
  { dias: 30, rotulo: "30 dias" },
];

const INTERVALO_ATUALIZACAO_MS = 10000;

// Cores dos gráficos (série única, validadas contra o fundo claro e o escuro do app).
const TEMA = {
  claro: { serie: "#2a78d6", texto: "#52514e", grade: "#e5e4e7", fundo: "#ffffff", cartao: "#f6f6f4" },
  escuro: { serie: "#3987e5", texto: "#c3c2b7", grade: "#2e303a", fundo: "#16171d", cartao: "#1f2028" },
};

function useTemaEscuro(): boolean {
  const consulta = "(prefers-color-scheme: dark)";
  const [escuro, setEscuro] = useState(() => window.matchMedia(consulta).matches);
  useEffect(() => {
    const media = window.matchMedia(consulta);
    const aoMudar = (e: MediaQueryListEvent) => setEscuro(e.matches);
    media.addEventListener("change", aoMudar);
    return () => media.removeEventListener("change", aoMudar);
  }, []);
  return escuro;
}

export default function Dashboard() {
  const [dias, setDias] = useState(1);
  const [dados, setDados] = useState<DashboardVendas | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [atualizadoEm, setAtualizadoEm] = useState<Date | null>(null);
  const cores = useTemaEscuro() ? TEMA.escuro : TEMA.claro;

  const carregar = useCallback(async () => {
    try {
      setDados(await getDashboardVendas(dias));
      setAtualizadoEm(new Date());
      setErro(null);
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : "Erro ao carregar o dashboard");
    }
  }, [dias]);

  // Polling simples a cada 10s (fácil de depurar) + atualização imediata quando uma comanda fecha.
  useEffect(() => {
    carregar();
    const intervalo = setInterval(carregar, INTERVALO_ATUALIZACAO_MS);
    return () => clearInterval(intervalo);
  }, [carregar]);

  useWebSocket(wsUrlParaStaff(), (evento) => {
    if (evento.tipo === "comanda_fechada") carregar();
  });

  const serie = dados?.serie.map((p) => ({ ...p, valor: Number(p.valor) })) ?? [];
  const produtos =
    dados?.top_produtos.map((p) => ({ rotulo: p.nome, quantidade: p.quantidade, valor: Number(p.valor) })) ?? [];
  const categorias =
    dados?.por_categoria.map((c) => ({ rotulo: c.categoria, quantidade: c.quantidade, valor: Number(c.valor) })) ?? [];
  const tituloSerie = dados?.granularidade === "dia" ? "Consumo por dia" : "Consumo por hora";

  return (
    <main style={{ maxWidth: 1000, margin: "3vh auto", padding: "0 16px", fontFamily: "sans-serif", textAlign: "left" }}>
      <p>
        <Link to="/admin">← voltar</Link>
      </p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center", justifyContent: "space-between" }}>
        <h1 style={{ margin: 0 }}>Vendas</h1>
        <div role="group" aria-label="Período" style={{ display: "flex", gap: 4 }}>
          {PERIODOS.map((p) => (
            <button
              key={p.dias}
              onClick={() => setDias(p.dias)}
              aria-pressed={dias === p.dias}
              style={{
                padding: "6px 12px",
                borderRadius: 6,
                border: `1px solid ${cores.grade}`,
                background: dias === p.dias ? cores.serie : "transparent",
                color: dias === p.dias ? "#fff" : "inherit",
                cursor: "pointer",
              }}
            >
              {p.rotulo}
            </button>
          ))}
        </div>
      </div>
      <p style={{ color: cores.texto, fontSize: 14 }}>
        {atualizadoEm ? `Atualizado às ${atualizadoEm.toLocaleTimeString("pt-BR")} · ` : ""}atualiza sozinho a cada
        10s
      </p>

      {erro && <p style={{ color: "crimson" }}>{erro}</p>}
      {!dados && !erro && <p>Carregando...</p>}

      {dados && (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(170px, 1fr))",
              gap: 12,
              margin: "16px 0 24px",
            }}
          >
            <Indicador cores={cores} rotulo="Faturamento" valor={formatarReais(dados.faturamento)} destaque />
            <Indicador cores={cores} rotulo="Comandas fechadas" valor={String(dados.comandas_fechadas)} />
            <Indicador cores={cores} rotulo="Ticket médio" valor={formatarReais(dados.ticket_medio)} />
            <Indicador cores={cores} rotulo="Taxa de serviço" valor={formatarReais(dados.taxa_servico)} />
            <Indicador
              cores={cores}
              rotulo="Consumo lançado"
              valor={formatarReais(dados.consumo)}
              detalhe={`${dados.itens_vendidos} itens`}
            />
            <Indicador cores={cores} rotulo="Comandas abertas agora" valor={String(dados.comandas_abertas_agora)} />
            <Indicador
              cores={cores}
              rotulo="Tempo médio de preparo"
              valor={formatarMinutos(dados.tempo_medio_preparo_min)}
            />
          </div>

          <Secao titulo={tituloSerie}>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={serie} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke={cores.grade} />
                <XAxis
                  dataKey="rotulo"
                  tick={{ fill: cores.texto, fontSize: 12 }}
                  stroke={cores.grade}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fill: cores.texto, fontSize: 12 }}
                  stroke={cores.grade}
                  tickFormatter={(v: number) => `R$ ${v}`}
                  width={70}
                />
                <Tooltip
                  cursor={{ fill: cores.grade, opacity: 0.4 }}
                  contentStyle={{ background: cores.fundo, border: `1px solid ${cores.grade}` }}
                  formatter={(valor) => [formatarReais(Number(valor)), "Consumo"]}
                />
                <Bar
                  dataKey="valor"
                  fill={cores.serie}
                  radius={[4, 4, 0, 0]}
                  maxBarSize={36}
                  isAnimationActive={false}
                />
              </BarChart>
            </ResponsiveContainer>
            <details>
              <summary style={{ cursor: "pointer", fontSize: 14 }}>Ver em tabela</summary>
              <table style={{ borderCollapse: "collapse", marginTop: 8, fontSize: 14 }}>
                <thead>
                  <tr>
                    <th style={celula}>{dados.granularidade === "dia" ? "Dia" : "Hora"}</th>
                    <th style={celula}>Itens</th>
                    <th style={celula}>Consumo</th>
                  </tr>
                </thead>
                <tbody>
                  {dados.serie
                    .filter((p) => p.itens !== 0)
                    .map((p) => (
                      <tr key={p.inicio}>
                        <td style={celula}>{p.rotulo}</td>
                        <td style={celula}>{p.itens}</td>
                        <td style={celula}>{formatarReais(p.valor)}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </details>
          </Secao>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 24 }}>
            <Secao titulo="Produtos mais vendidos">
              {produtos.length === 0 ? (
                <p>Nenhuma venda no período.</p>
              ) : (
                <RankingHorizontal dados={produtos} cores={cores} />
              )}
            </Secao>
            <Secao titulo="Vendas por categoria">
              {categorias.length === 0 ? (
                <p>Nenhuma venda no período.</p>
              ) : (
                <RankingHorizontal dados={categorias} cores={cores} />
              )}
            </Secao>
          </div>
        </>
      )}
    </main>
  );
}

type Cores = (typeof TEMA)["claro"];

function formatarMinutos(minutos: number | null): string {
  if (minutos === null) return "—";
  if (minutos < 1) return "menos de 1 min";
  return `${minutos.toLocaleString("pt-BR")} min`;
}

interface LinhaRanking {
  rotulo: string;
  quantidade: number;
  valor: number;
}

function RankingHorizontal({ dados, cores }: { dados: LinhaRanking[]; cores: Cores }) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(120, dados.length * 36)}>
      <BarChart data={dados} layout="vertical" margin={{ top: 0, right: 90, left: 8, bottom: 0 }}>
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="rotulo"
          width={150}
          tick={{ fill: cores.texto, fontSize: 13 }}
          stroke={cores.grade}
        />
        <Tooltip
          cursor={{ fill: cores.grade, opacity: 0.4 }}
          contentStyle={{ background: cores.fundo, border: `1px solid ${cores.grade}` }}
          formatter={(valor, _nome, item) => [
            `${formatarReais(Number(valor))} (${(item.payload as LinhaRanking).quantidade} un.)`,
            "Vendido",
          ]}
        />
        <Bar dataKey="valor" fill={cores.serie} radius={[0, 4, 4, 0]} maxBarSize={22} isAnimationActive={false}>
          <LabelList
            dataKey="valor"
            position="right"
            fill={cores.texto}
            fontSize={12}
            formatter={(valor) => formatarReais(Number(valor))}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function Indicador({
  rotulo,
  valor,
  detalhe,
  destaque,
  cores,
}: {
  rotulo: string;
  valor: string;
  detalhe?: string;
  destaque?: boolean;
  cores: Cores;
}) {
  return (
    <div style={{ background: cores.cartao, borderRadius: 8, padding: 12 }}>
      <div style={{ fontSize: 13, color: cores.texto }}>{rotulo}</div>
      <div style={{ fontSize: destaque ? 26 : 22, fontWeight: 600, marginTop: 4 }}>{valor}</div>
      {detalhe && <div style={{ fontSize: 13, color: cores.texto }}>{detalhe}</div>}
    </div>
  );
}

function Secao({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section style={{ marginBottom: 24 }}>
      <h2 style={{ fontSize: 18 }}>{titulo}</h2>
      {children}
    </section>
  );
}

const celula: React.CSSProperties = { borderBottom: "1px solid #8884", padding: "4px 12px", textAlign: "left" };
