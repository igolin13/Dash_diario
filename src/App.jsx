import { useEffect, useState } from "react";
import { Factory, Boxes, ShieldCheck, Wrench, ClipboardList, Radio, AlertCircle, TrendingUp, TrendingDown, Bot } from "lucide-react";

import { COLORS, corPelaMeta } from "./components/colors";
import { Gauge } from "./components/Gauge";
import { Panel } from "./components/Panel";
import { Stat, EmptyState, BarRow } from "./components/Stat";
import { FiltroData } from "./components/FiltroData";
import { useApiResource } from "./hooks/useApiResource";
import { fetchKpis, fetchProducaoPorLinha, fetchCorretivaPorLinha, fetchEstoqueVencido, fetchOpsAbertas, fetchQualidade, fetchAderenciaResumo } from "./lib/api";

/* ---------------------------------------------------------
   APP — Dash Diário Incoflandres
   Hero (OEE/Performance/Disponibilidade/Produção/Perdas/Corretiva) e
   o painel de Litografia (quantidade por linha) vêm 100% da API real
   (FastAPI + SQL Server). Os demais painéis (Estoque, Manutenção por
   linha, Qualidade, PCP) ainda não têm endpoint conectado — mostram
   um estado vazio honesto em vez de dado inventado.
--------------------------------------------------------- */
export default function App() {
  // Relógio ao vivo (só visual, não afeta qual dia é consultado na API)
  const [horaAtual, setHoraAtual] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setHoraAtual(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  const hh = String(horaAtual.getHours()).padStart(2, "0");
  const mm = String(horaAtual.getMinutes()).padStart(2, "0");
  const ss = String(horaAtual.getSeconds()).padStart(2, "0");

  // Data selecionada pelo filtro — é ela que decide qual dia a API consulta
  const [dataSelecionada, setDataSelecionada] = useState(new Date());

  const { data, loading, error, atualizadoEm, recarregar } = useApiResource(fetchKpis, dataSelecionada);
  const {
    data: producaoLinha,
    loading: loadingLinha,
    error: errorLinha,
  } = useApiResource(fetchProducaoPorLinha, dataSelecionada);

  const { data: corretivaLinha, 
    loading: loadingCorretiva,
     error: errorCorretiva 
    } = useApiResource(fetchCorretivaPorLinha,dataSelecionada);

  // Estoque é "vivo" (sem histórico por dia) — não depende da data
  // selecionada no filtro, por isso passa uma dependência fixa (null).
  const {
    data: estoque,
    loading: loadingEstoque,
    error: errorEstoque,
  } = useApiResource(fetchEstoqueVencido, null);

  const {
    data: opsAbertas,
    loading: loadingOps,
    error: errorOps,
  } = useApiResource(fetchOpsAbertas, null);

  // Qualidade depende da data selecionada (RNC's no mês usa o mês dela).
  const {
    data: qualidade,
    loading: loadingQualidade,
    error: errorQualidade,
  } = useApiResource(fetchQualidade, dataSelecionada);

  // Aderência de PCP — só faz sentido pra dias já fechados (o próprio
  // fetchAderenciaResumo bloqueia hoje/futuro antes de bater na rede).
  const {
    data: aderencia,
    loading: loadingAderencia,
    error: errorAderencia,
  } = useApiResource(fetchAderenciaResumo, dataSelecionada);

  // Conversões pra percentual (a API devolve fração 0-1)
  const oeeValor = data?.oee?.valor != null ? data.oee.valor * 100 : null;
  const oeeMeta = data?.oee?.meta != null ? data.oee.meta * 100 : null;
  const perfValor = data?.performance?.valor != null ? data.performance.valor * 100 : null;
  const perfMeta = data?.performance?.meta != null ? data.performance.meta * 100 : null;
  const dispValor = data?.disponibilidade_producao?.valor != null ? data.disponibilidade_producao.valor * 100 : null;
  const dispMeta = data?.disponibilidade_producao?.meta != null ? data.disponibilidade_producao.meta * 100 : null;
  const corretivaValor = data?.corretiva?.valor != null ? data.corretiva.valor * 100 : null;
  const corretivaMeta = data?.corretiva?.meta != null ? data.corretiva.meta * 100 : null;
  const percPerdas = data?.perc_perdas != null ? (data.perc_perdas * 100).toFixed(2).replace(".", ",") + "%" : null;
  const producaoTotal = data?.producao_total != null ? Math.round(data.producao_total).toLocaleString("pt-BR") : null;

  // "vs. dia anterior" — vem da API (Medida_OEE_Dia_Anterior), nunca inventado
  const variacaoPP = data?.oee_dia_anterior?.variacao_pp;
  const temVariacao = variacaoPP != null && !Number.isNaN(variacaoPP);
  const variacaoPositiva = temVariacao && variacaoPP >= 0;

  const impressoras = producaoLinha?.impressoras || [];
  const envernizadeiras = producaoLinha?.envernizadeiras || [];
  const impressorasMax = Math.max(1, ...impressoras.map((d) => d.quantidade));
  const envernizadeirasMax = Math.max(1, ...envernizadeiras.map((d) => d.quantidade));

  // Máquinas com 0% ficam fora da lista de Corretiva.
  const corretivaLista = (corretivaLinha || []).filter((d) => d.percentual > 0);
  const corretivaMax = Math.max(1, ...corretivaLista.map((d) => d.percentual));

  return (
    <div
      className="min-h-screen w-full"
      style={{
        background: `radial-gradient(1200px 600px at 15% -10%, #14243D 0%, ${COLORS.bg} 55%)`,
        color: COLORS.text,
        fontFamily: "Inter, ui-sans-serif, system-ui",
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');
        .font-mono { font-family: 'IBM Plex Mono', monospace; }
        @keyframes pulse-dot { 0%,100% { opacity:1; box-shadow:0 0 0 0 rgba(207,161,53,.5);} 50% {opacity:.55; box-shadow:0 0 0 5px rgba(207,161,53,0);} }
        .live-dot { animation: pulse-dot 2s ease-in-out infinite; }
        @keyframes scan { 0% { transform: translateY(-100%);} 100% { transform: translateY(100%);} }
        .scanline::after {
          content:""; position:absolute; inset:0; pointer-events:none; overflow:hidden;
          background: linear-gradient(180deg, transparent 0%, rgba(233,197,103,0.06) 45%, rgba(233,197,103,0.12) 50%, rgba(233,197,103,0.06) 55%, transparent 100%);
          animation: scan 5s linear infinite;
        }
      `}</style>

      {/* TOP BAR */}
      <div
        className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5"
        style={{ borderBottom: `1px solid ${COLORS.border}`, background: "#0C1526" }}
      >
        <div className="flex items-center gap-3">
          <img src="/LOGO CINBAL-INCO.png" alt="Logo Incoflandres" className="w-36 h-auto object-contain" />
          <div>
            <div className="text-[25px] font-semibold tracking-[0.02em]" style={{ fontFamily: "Oswald, sans-serif" }}>
              Gestão Industrial
            </div>
            <div className="text-[15px]" style={{ color: COLORS.textMuted }}>
              Resumo diário de performance
            </div>
          </div>
        </div>

        <div className="flex items-center gap-5">
          <FiltroData dataSelecionada={dataSelecionada} onMudarData={setDataSelecionada} />
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full live-dot" style={{ background: error ? COLORS.red : COLORS.gold }} />
            <span className="text-[11.5px] uppercase tracking-[0.14em]" style={{ color: error ? COLORS.red : COLORS.gold, fontFamily: "Oswald, sans-serif" }}>
              {error ? "Sem conexão com a API" : "Ao vivo"}
            </span>
          </div>
          <div className="font-mono text-[14px]" style={{ color: COLORS.text }}>
            {hh}:{mm}
            <span style={{ color: COLORS.textFaint }}>:{ss}</span>
          </div>
        </div>
      </div>

      {/* AVISO DE ERRO — API fora do ar. Nunca cai pra dado mockado. */}
      {error && (
        <div className="mx-5 mt-5 flex items-center gap-2.5 px-4 py-3 rounded-sm" style={{ background: `${COLORS.red}14`, border: `1px solid ${COLORS.red}55` }}>
          <AlertCircle size={16} style={{ color: COLORS.red }} />
          <span className="text-[13.5px]" style={{ color: COLORS.text }}>
            Não foi possível buscar os dados reais da API ({error}). Confere se o backend está rodando em{" "}
            <code className="font-mono">{import.meta.env.VITE_API_URL || "http://localhost:8000"}</code>.
          </span>
          <button
            onClick={recarregar}
            className="ml-auto text-[12px] uppercase tracking-wider px-2.5 py-1 rounded-[2px] shrink-0"
            style={{ background: `${COLORS.red}22`, color: COLORS.red, border: `1px solid ${COLORS.red}55` }}
          >
            Tentar de novo
          </button>
        </div>
      )}

      {/* HERO — OEE (100% dado real da API) */}
      <div
        className="relative overflow-hidden mx-5 mt-5 rounded-sm scanline"
        style={{ background: "linear-gradient(135deg, #101B30 0%, #0D1727 100%)", border: `1px solid ${COLORS.border}` }}
      >
        <div className="relative px-6 pt-5 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="w-1 h-4 rounded-full" style={{ background: COLORS.gold }} />
            <h1 className="text-[14.5px] font-semibold uppercase tracking-[0.16em]" style={{ color: COLORS.goldBright, fontFamily: "Oswald, sans-serif" }}>
              Central de Controle Operacional - Produção
            </h1>
          </div>
          {atualizadoEm && (
            <span className="text-[14px]" style={{ color: COLORS.text }}>
              Atualizado em {atualizadoEm.toLocaleTimeString("pt-BR")}
            </span>
          )}
        </div>

        <div className="relative grid grid-cols-1 md:grid-cols-[auto_1px_1fr] gap-6 md:gap-8 p-6 pt-4 items-center">
          <div className="flex items-center gap-6">
            <Gauge value={oeeValor} meta={oeeMeta} label="Índice de OEE" size={150} big />
            <div>
              {temVariacao && (
                <div
                  className="flex items-center gap-1.5 text-[12px] px-2 py-1 rounded-[2px] w-fit"
                  style={{
                    background: `${variacaoPositiva ? COLORS.green : COLORS.red}1A`,
                    border: `1px solid ${variacaoPositiva ? COLORS.green : COLORS.red}55`,
                    color: variacaoPositiva ? COLORS.green : COLORS.red,
                  }}
                >
                  {variacaoPositiva ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                  {variacaoPositiva ? "+" : ""}
                  {(variacaoPP * 100).toFixed(1).replace(".", ",")}pp vs. dia anterior
                </div>
              )}
              <p className="mt-3 text-[13.5px] max-w-[220px]" style={{ color: COLORS.textMuted }}>
                Eficiência global do equipamento
                {oeeMeta != null && ` meta: ${oeeMeta.toFixed(0)}%`}
              </p>
            </div>
          </div>

          <div className="hidden md:block h-full" style={{ background: COLORS.border }} />

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
            <Gauge value={perfValor} meta={perfMeta} label="Performance" />
            <Gauge value={dispValor} meta={dispMeta} label="Disponibilidade" />
            <div className="flex flex-col justify-center gap-3">
              <Stat label="Produção total" value={producaoTotal} />
              <Stat
                label="Eficiência de setup"
                value={data?.eficiencia_setup?.valor != null ? `${(data.eficiencia_setup.valor * 100).toFixed(0)}%` : null}
                sub={data && data.eficiencia_setup?.valor == null ? "Em definição" : undefined}
              />
            </div>
            <div className="flex flex-col justify-center gap-3">
              <Stat label="Perdas" value={percPerdas} />
              <Stat
                label="Corretiva"
                value={corretivaValor != null ? `${corretivaValor.toFixed(2).replace(".", ",")}%` : null}
                color={corretivaValor != null ? corPelaMeta(corretivaValor, corretivaMeta, true) : undefined}
                sub={corretivaMeta != null ? `meta ≤ ${corretivaMeta.toFixed(0)}%` : undefined}
              />
            </div>
          </div>
        </div>
      </div>

      {/* GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 p-5">
        {/* LITOGRAFIA — quantidade produzida por linha, dado real da API */}
        <Panel icon={Factory} title="Litografia" tone="steel" className="lg:row-span-2">
          {errorLinha ? (
            <EmptyState mensagem={`Falha ao buscar produção por linha (${errorLinha})`} />
          ) : !loadingLinha && impressoras.length === 0 && envernizadeiras.length === 0 ? (
            <EmptyState mensagem="Sem produção registrada nas linhas ativas para essa data" />
          ) : (
            <>
              <div className="flex-1 flex flex-col">
                <div className="text-[14px] uppercase tracking-[0.1em] mb-3" style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}>
                  Impressoras · quantidade produzida
                </div>
                <div className="flex-1 flex flex-col justify-evenly">
                  {impressoras.map((d) => (
                    <BarRow
                      key={d.linha}
                      label={d.linha}
                      value={d.quantidade}
                      max={impressorasMax}
                      color={COLORS.steel}
                      format={(v) => Math.round(v).toLocaleString("pt-BR")}
                    />
                  ))}
                </div>
              </div>
              <div className="flex-1 flex flex-col" style={{ borderTop: `1px solid ${COLORS.borderSoft}`, paddingTop: 14 }}>
                <div className="text-[14px] uppercase tracking-[0.1em] mb-3" style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}>
                  Envernizadeiras · quantidade produzida
                </div>
                <div className="flex-1 flex flex-col justify-evenly">
                  {envernizadeiras.map((d) => (
                    <BarRow
                      key={d.linha}
                      label={d.linha}
                      value={d.quantidade}
                      max={envernizadeirasMax}
                      color={COLORS.gold}
                      format={(v) => Math.round(v).toLocaleString("pt-BR")}
                    />
                  ))}
                </div>
              </div>
            </>
          )}
        </Panel>

        <Panel
          icon={Boxes}
          title="Estoque"
          tone="steel"
          badge={
            <span
              className="text-[9.5px] uppercase tracking-wider px-1.5 py-0.5 rounded-[2px]"
              style={{ background: `${COLORS.steel}22`, color: COLORS.steel, border: `1px solid ${COLORS.steel}55` }}
            >
              tempo real
            </span>
          }
        >
          {errorEstoque ? (
            <EmptyState mensagem={`Falha ao buscar estoque (${errorEstoque})`} />
          ) : !loadingEstoque && !estoque ? (
            <EmptyState mensagem="Sem dados de estoque disponíveis" />
          ) : (
            <>
              <div
                className="text-[14.5px] uppercase tracking-[0.1em]"
                style={{ color: COLORS.textFaint, fontFamily: "Oswald, sans-serif", borderTop: `1px solid ${COLORS.borderSoft}`, paddingTop: 10 }}
              >
                Estoque vencido
              </div>
              <div className="grid grid-cols-4 gap-2 items-end">
                <div>
                  <div className="font-mono font-semibold text-base leading-none" style={{ color: COLORS.text }}>
                    {estoque ? Math.round(estoque.buckets["30-60"]).toLocaleString("pt-BR") : "—"}
                  </div>
                  <div className="mt-1 text-[12px] uppercase tracking-[0.08em]" style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}>
                    30-60 dias
                  </div>
                </div>
                <div>
                  <div className="font-mono font-semibold text-base leading-none" style={{ color: COLORS.text }}>
                    {estoque ? Math.round(estoque.buckets["60-90"]).toLocaleString("pt-BR") : "—"}
                  </div>
                  <div className="mt-1 text-[12px] uppercase tracking-[0.08em]" style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}>
                    60-90 dias
                  </div>
                </div>
                <div>
                  <div className="font-mono font-semibold text-base leading-none" style={{ color: COLORS.text }}>
                    {estoque ? Math.round(estoque.buckets[">90"]).toLocaleString("pt-BR") : "—"}
                  </div>
                  <div className="mt-1 text-[12px] uppercase tracking-[0.08em]" style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}>
                    &gt; 90 dias
                  </div>
                </div>
                <div className="pl-2" style={{ borderLeft: `1px solid ${COLORS.borderSoft}` }}>
                  <div className="font-mono font-bold text-xl leading-none" style={{ color: COLORS.gold }}>
                    {estoque ? Math.round(estoque.estoque_vencido_total).toLocaleString("pt-BR") : "—"}
                  </div>
                  <div className="mt-1 text-[11px] uppercase tracking-[0.08em] font-semibold" style={{ color: COLORS.goldBright, fontFamily: "Oswald, sans-serif" }}>
                    Total
                  </div>
                </div>
              </div>

              <div
                className="text-[14.5px] uppercase tracking-[0.1em]"
                style={{ color: COLORS.textFaint, fontFamily: "Oswald, sans-serif", borderTop: `1px solid ${COLORS.borderSoft}`, paddingTop: 10 }}
              >
                OP's em aberto (+5 dias)
              </div>
              {errorOps ? (
                <p className="text-[10.5px]" style={{ color: COLORS.red }}>
                  Falha ao buscar OP's em aberto ({errorOps})
                </p>
              ) : (
                <div className="font-mono font-bold text-xl leading-none" style={{ color: COLORS.text }}>
                  {!loadingOps && opsAbertas ? opsAbertas.total.toLocaleString("pt-BR") : "—"}
                </div>
              )}
            </>
          )}
        </Panel>

      <Panel icon={Wrench} title="Manutenção" tone="red">
          {errorCorretiva ? (
            <EmptyState mensagem={`Falha ao buscar corretiva por linha (${errorCorretiva})`} />
          ) : !loadingCorretiva && corretivaLista.length === 0 ? (
            <EmptyState mensagem="Sem paradas corretivas registradas para essa data" />
          ) : (
            <div className="flex-1 flex flex-col justify-evenly">
              {corretivaLista.map((d) => (
                <BarRow
                  key={d.linha}
                  label={d.linha}
                  value={d.percentual}
                  max={corretivaMax}
                  color={d.percentual >= 30 ? COLORS.red : COLORS.amber}
                  format={(v) => `${v.toFixed(1).replace(".", ",")}%`}
                  flag={d.percentual >= 30 ? "CRÍTICO" : undefined}
                />
              ))}
            </div>
          )}
        </Panel>

        <Panel icon={ShieldCheck} title="Qualidade" tone="gold">
          {errorQualidade ? (
            <EmptyState mensagem={`Falha ao buscar indicadores de Qualidade (${errorQualidade})`} />
          ) : !loadingQualidade && !qualidade ? (
            <EmptyState mensagem="Sem dados de Qualidade disponíveis" />
          ) : (
            <>
              <div
                className="text-[13px] uppercase tracking-[0.1em]"
                style={{ color: COLORS.textFaint, fontFamily: "Oswald, sans-serif" }}
              >
                Sistema de Gestão da Qualidade
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="font-mono font-bold text-xl leading-none" style={{ color: COLORS.red }}>
                    {qualidade ? qualidade.rnc_abertas.toLocaleString("pt-BR") : "—"}
                  </div>
                  <div className="mt-1 text-[12px] uppercase tracking-[0.08em]" style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}>
                    RNC's em aberto
                  </div>
                  <div className="text-[11px]" style={{ color: COLORS.textFaint }}>
                    Aguardando resposta
                  </div>
                </div>
                <div className="pl-3" style={{ borderLeft: `1px solid ${COLORS.borderSoft}` }}>
                  <div className="font-mono font-semibold text-xl leading-none" style={{ color: COLORS.text }}>
                    {qualidade ? qualidade.rnc_no_mes.toLocaleString("pt-BR") : "—"}
                  </div>
                  <div className="mt-1 text-[12px] uppercase tracking-[0.08em]" style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}>
                    RNC's no mês
                  </div>
                  {qualidade?.mes_referencia && (
                    <div className="text-[11px] capitalize" style={{ color: COLORS.textFaint }}>
                      {new Date(qualidade.mes_referencia + "-02").toLocaleDateString("pt-BR", { month: "long", year: "numeric" })}
                    </div>
                  )}
                </div>
              </div>

              <div
                className="text-[13px] uppercase tracking-[0.1em]"
                style={{ color: COLORS.textFaint, fontFamily: "Oswald, sans-serif", borderTop: `1px solid ${COLORS.borderSoft}`, paddingTop: 10 }}
              >
                Controle de Qualidade
              </div>
              <div>
                <div className="font-mono font-semibold text-xl leading-none" style={{ color: COLORS.amber }}>
                  {qualidade ? qualidade.fardos_retidos.toLocaleString("pt-BR") : "—"}
                </div>
                <div className="mt-1 text-[12px] uppercase tracking-[0.08em]" style={{ color: COLORS.textMuted, fontFamily: "Oswald, sans-serif" }}>
                  Fardos retidos
                </div>
              </div>
            </>
          )}
        </Panel>

        <Panel icon={ClipboardList} title="PCP" tone="steel">
          {errorAderencia ? (
            <EmptyState mensagem={errorAderencia} />
          ) : !loadingAderencia && !aderencia ? (
            <EmptyState mensagem="Sem dados de aderência disponíveis" />
          ) : aderencia?.erro ? (
            <EmptyState mensagem={aderencia.erro} />
          ) : (
            <>
              <div className="grid grid-cols-2 gap-3">
                <Stat
                  label="Aderência de quantidade"
                  value={aderencia?.aderencia_quantidade != null ? `${(aderencia.aderencia_quantidade * 100).toFixed(1)}%` : null}
                />
                <Stat
                  label="OPs reprogramadas"
                  value={aderencia?.total_ops_reprogramadas != null ? String(aderencia.total_ops_reprogramadas) : null}
                  sub={aderencia ? `de ${aderencia.total_ops_planejadas} planejadas` : undefined}
                />
              </div>
              {aderencia?.resumo_ia && (
                <div style={{ borderTop: `1px solid ${COLORS.borderSoft}`, paddingTop: 10 }}>
                  <div
                    className="flex items-center gap-1.5 text-[9.5px] uppercase tracking-wider mb-1.5"
                    style={{ color: COLORS.textFaint, fontFamily: "Oswald, sans-serif" }}
                  >
                    <Bot size={11} style={{ color: COLORS.textFaint }} />
                    Análise gerada por assistente virtual
                  </div>
                  <p className="text-[11px] leading-relaxed" style={{ color: COLORS.textMuted }}>
                    {aderencia.resumo_ia}
                  </p>
                </div>
              )}
              {aderencia?.resumo_ia_erro && (
                <p className="text-[10px]" style={{ color: COLORS.textFaint }}>
                  Resumo da IA indisponível ({aderencia.resumo_ia_erro})
                </p>
              )}
            </>
          )}
        </Panel>
      </div>

      <div className="flex items-center gap-1.5 justify-center pb-6 opacity-60">
        <Radio size={11} style={{ color: COLORS.textFaint }} />
        <span className="text-[12px]" style={{ color: COLORS.textFaint }}>
          Inteligência de negócios · Grupo Incoflandres {loading && "· carregando..."}
        </span>
      </div>
    </div>
  );
}