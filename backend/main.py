"""
API que expõe os KPIs reais (SQL Server) pro Dash Diário em React.

Rodar:
    uvicorn main:app --reload --port 8000

Endpoint principal:
    GET /api/kpis?data_inicio=2026-08-01&data_fim=2026-08-14
"""
from datetime import date

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from database import fetch_base_quantidade, fetch_base_tempo
from kpis import montar_kpis, debug_breakdown, producao_por_linha

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
    return montar_kpis(df_qtd, df_tempo)


@app.get("/api/producao-por-linha")
def get_producao_por_linha(
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
):
    """Quantidade Produzida por linha (impressoras/envernizadeiras),
    já filtrado pras 8 linhas ativas — alimenta o painel Litografia."""
    df_qtd = fetch_base_quantidade(data_inicio, data_fim)
    return producao_por_linha(df_qtd)


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