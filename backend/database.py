"""
Camada de acesso a dados. Busca as duas views reais do SQL Server
e devolve DataFrames já tipados e categorizados nas colunas usadas
pelos KPIs.
"""
import datetime as dt

import pandas as pd
from sqlalchemy import create_engine, text

from categorizacao import analise_gerencial, analise_nova
from config import build_connection_string, VIEW_QUANTIDADE, VIEW_TEMPO

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(build_connection_string(), fast_executemany=True)
    return _engine


def _fim_do_dia(data_fim):
    """BETWEEN com uma data 'pura' só pega meia-noite exata; isso estende
    o limite superior até o fim do dia, pra cobrir o dia inteiro."""
    return dt.datetime.combine(data_fim, dt.time(23, 59, 59))


def _para_horas(valor) -> float:
    """Converte T.Decorrido/Meta Setup para horas decimais.

    O SQL Server manda essas colunas como TIME, que o pyodbc converte
    pra datetime.time (não string) — por isso não dá pra usar
    pd.to_timedelta direto nelas.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return 0.0
    if isinstance(valor, dt.time):
        return (valor.hour * 3600 + valor.minute * 60 + valor.second + valor.microsecond / 1e6) / 3600
    if isinstance(valor, dt.timedelta):
        return valor.total_seconds() / 3600
    td = pd.to_timedelta(str(valor), errors="coerce")
    return td.total_seconds() / 3600 if pd.notna(td) else 0.0


# ---------- VW_BASE_QUANTIDADE ----------
QUANTIDADE_COLS = [
    "Apelido Recurso", "OP Mãe", "Cód. da Ordem", "Operação", "Nome Produto",
    "Turno", "Início", "Término", "Velocidade Padrão", "Quantidade Produzida",
    "Perdas", "Retrabalho", "Quantidade total", "Data de Produção",
    "Semana", "Mês", "Cliente", "Ano",
]


def fetch_base_quantidade(data_inicio=None, data_fim=None) -> pd.DataFrame:
    query = f'SELECT {", ".join(f"[{c}]" for c in QUANTIDADE_COLS)} FROM {VIEW_QUANTIDADE}'
    params = {}
    if data_inicio and data_fim:
        query += ' WHERE [Data de Produção] BETWEEN :data_inicio AND :data_fim'
        params = {"data_inicio": data_inicio, "data_fim": _fim_do_dia(data_fim)}

    df = pd.read_sql(text(query), get_engine(), params=params or None)
    for col in ["Quantidade Produzida", "Perdas", "Retrabalho", "Quantidade total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


# ---------- VW_BASE_TEMPO ----------
# Não busca mais a coluna "Análise Gerencial" do SQL Server — ela está
# desatualizada lá (o Power BI ignora e recalcula do zero, ver
# categorizacao.py). "Análise Nova" nunca existiu como coluna SQL.
TEMPO_COLS = [
    "Apelido Recurso", "Cód. da Ordem", "(R)Início", "Término", "T.Decorrido",
    "Nome Status Recurso", "(R)Nome Detalhe", "Cód. Produto", "Nome Produto",
    "(R)G0015.DTPROD", "Semana", "Mês", "Meta Setup", "Turno", "Setup", "Ano",
]


def fetch_base_tempo(data_inicio=None, data_fim=None) -> pd.DataFrame:
    query = f'SELECT {", ".join(f"[{c}]" for c in TEMPO_COLS)} FROM {VIEW_TEMPO}'
    params = {}
    if data_inicio and data_fim:
        # Filtra por (R)G0015.DTPROD (dia de produção "oficial", já ajusta
        # turno que atravessa meia-noite) — não (R)Início, timestamp cru.
        query += ' WHERE [(R)G0015.DTPROD] BETWEEN :data_inicio AND :data_fim'
        params = {"data_inicio": data_inicio, "data_fim": _fim_do_dia(data_fim)}

    df = pd.read_sql(text(query), get_engine(), params=params or None)

    df["T.Decorrido (h)"] = df["T.Decorrido"].apply(_para_horas)
    df["Meta Setup (h)"] = df["Meta Setup"].apply(_para_horas)

    # Recalcula as duas categorizações em Python (ver categorizacao.py).
    df["Análise Gerencial"] = df.apply(
        lambda r: analise_gerencial(r["Nome Status Recurso"], r["(R)Nome Detalhe"]), axis=1
    )
    df["Análise Nova"] = df["(R)Nome Detalhe"].apply(analise_nova)

    return df