"""
API que expõe os KPIs reais (SQL Server) pro Dash Diário em React.

Rodar:
    uvicorn main:app --reload --port 8000

Endpoint principal:
    GET /api/kpis?data_inicio=2026-08-01&data_fim=2026-08-14
"""
from datetime import date, timedelta

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from database import fetch_base_quantidade, fetch_base_tempo
from kpis import montar_kpis, debug_breakdown, producao_por_linha, corretiva_por_linha
from estoque import estoque_vencido

app = FastAPI(title="Dash Diário — Incoflandres API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # ajuste para o domínio real em produção
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/kpis")
def get_kpis(
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
):
    df_qtd = fetch_base_quantidade(data_inicio, data_fim)
    df_tempo = fetch_base_tempo(data_inicio, data_fim)
    kpis = montar_kpis(df_qtd, df_tempo)

    # "vs. dia anterior" — réplica de Medida_OEE_Dia_Anterior (DATEADD -1 DAY)
    # no BI original: variação é diferença em pontos percentuais, não % relativo.
    # Envolto em try/except: se o dia anterior não tiver dado (ou o SQL
    # falhar por qualquer motivo), o dia principal continua respondendo
    # normalmente — só a comparação fica ausente.
    kpis["oee_dia_anterior"] = None
    if data_inicio and data_fim:
        try:
            dia_anterior = data_inicio - timedelta(days=1)
            df_qtd_ant = fetch_base_quantidade(dia_anterior, dia_anterior)
            df_tempo_ant = fetch_base_tempo(dia_anterior, dia_anterior)
            oee_ontem = montar_kpis(df_qtd_ant, df_tempo_ant)["oee"]["valor"]
            oee_hoje = kpis["oee"]["valor"]
            kpis["oee_dia_anterior"] = {
                "valor": oee_ontem,
                "variacao_pp": (oee_hoje - oee_ontem) if (oee_hoje is not None and oee_ontem) else None,
            }
        except Exception as erro:
            print(f"[api/kpis] Falha ao buscar dia anterior ({erro}); seguindo sem a comparação.")

    return kpis


@app.get("/api/producao-por-linha")
def get_producao_por_linha(
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
):
    """Quantidade Produzida por linha (impressoras/envernizadeiras),
    já filtrado pras 8 linhas ativas — alimenta o painel Litografia."""
    df_qtd = fetch_base_quantidade(data_inicio, data_fim)
    return producao_por_linha(df_qtd)


@app.get("/api/corretiva-por-linha")
def get_corretiva_por_linha(
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
):
    """% de tempo em manutenção corretiva por linha — alimenta o painel Manutenção."""
    df_tempo = fetch_base_tempo(data_inicio, data_fim)
    return corretiva_por_linha(df_tempo)


@app.get("/api/estoque-vencido")
def get_estoque_vencido():
    """Estoque vencido por faixa de dias (30-60 / 60-90 / >90).

    NÃO aceita data_inicio/data_fim — a base de estoque é viva (sem
    histórico por dia), sempre reflete o momento atual."""
    return estoque_vencido()


@app.get("/api/kpis/debug")
def get_kpis_debug(
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
):
    """Expõe todos os tempos/números intermediários — usar pra comparar
    linha a linha contra o Power BI quando os indicadores não baterem."""
    df_qtd = fetch_base_quantidade(data_inicio, data_fim)
    df_tempo = fetch_base_tempo(data_inicio, data_fim)
    return debug_breakdown(df_qtd, df_tempo)


@app.get("/health")
def health():
    return {"status": "ok"}