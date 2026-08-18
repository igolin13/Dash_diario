"""
Painel de Estoque — schema PROTHEUS_PRD, view VW_ESTOQUE.

Tradução exata dos filtros que já existiam na query M (Power Query) do
Igor. Diferente dos painéis de Litografia/Manutenção, esse painel NÃO
respeita o filtro de data do dashboard — a base de estoque é "viva"
(sobrescreve o valor a cada movimentação, sem manter foto histórica por
dia), então só faz sentido mostrar o estado ATUAL.

⚠️ B1_GRUPO = "2300": a query M original inclui esse grupo no filtro,
mas o Igor só definiu a coluna de quantidade para "1100" (BOBINA
METALICA → B8_SALDO) e "2100"/"2200" (FOLHA VIRGEM RETA/SCROLL →
B8_SALDO2). Linhas do grupo 2300 são buscadas mas ficam de fora de
qualquer soma — aparecem em "grupos_nao_classificados" no retorno da
API pra não silenciar o problema. Confirme com o Igor antes de assumir
qual coluna usar.

⚠️ Buckets de envelhecimento: "vencido" = tudo acima de 30 dias. Os 3
buckets nomeados (30-60 / 60-90 / >90) cobrem exatamente essa faixa —
"estoque_vencido_total" é simplesmente a soma dos 3, sem sobra.

Convenção de fronteira usada: 30 ≤ dias < 60 | 60 ≤ dias < 90 | dias ≥ 90.
"""
import datetime as dt

import pandas as pd
from sqlalchemy import create_engine, text

from config import build_connection_string_estoque, VIEW_ESTOQUE

_engine = None

GRUPOS = {
    "1100": "BOBINA METALICA",
    "2100": "FOLHA VIRGEM RETA",
    "2200": "FOLHA VIRGEM SCROLL",
}

FILIAIS_EXCLUIDAS = ("010102", "030101")
GRUPOS_FILTRO = ("1100", "2100", "2200", "2300")  # 2300 incluído p/ paridade com a query M
PROPRIETARIOS = ("000056", "000693")
COMPRADORES_EXCLUIDOS = (
    "CSN", "GDC ALIMENTOS S/A", "INCO GUARULHOS", "INCO PIN", "INCO VR", "MASAFER",
)

COLUNAS = [
    "B8_FILIAL", "B1_GRUPO", "BM_DESC", "B8_DATA", "B8_SALDO", "B8_SALDO2",
    "B8_LOTECTL", "B8_LOCAL", "B8_XXPROPR", "NOME_COMPRADOR",
]


def get_engine_estoque():
    global _engine
    if _engine is None:
        _engine = create_engine(build_connection_string_estoque(), fast_executemany=True)
    return _engine


def fetch_estoque() -> pd.DataFrame:
    """Busca VW_ESTOQUE já filtrada no SQL (mesmos filtros da query M
    original), exceto o filtro de B8_LOCAL (feito em pandas, porque o
    valor vem com espaços de preenchimento fixo — "10    " — e é mais
    seguro comparar já sem espaço)."""
    filiais = ",".join(f"'{f}'" for f in FILIAIS_EXCLUIDAS)
    grupos = ",".join(f"'{g}'" for g in GRUPOS_FILTRO)
    proprietarios = ",".join(f"'{p}'" for p in PROPRIETARIOS)
    compradores = ",".join(f"'{c}'" for c in COMPRADORES_EXCLUIDOS)

    query = f"""
        SELECT {", ".join(f"[{c}]" for c in COLUNAS)}
        FROM {VIEW_ESTOQUE} WITH (NOLOCK)
        WHERE [B8_FILIAL] NOT IN ({filiais})
          AND [B1_GRUPO] IN ({grupos})
          AND [B8_XXPROPR] IN ({proprietarios})
          AND [B8_SALDO] <> 0
          AND [NOME_COMPRADOR] NOT IN ({compradores})
    """

    df = pd.read_sql(text(query), get_engine_estoque())

    # B8_LOCAL vem com espaço de preenchimento fixo (CHAR) — remove antes de comparar.
    df = df[df["B8_LOCAL"].astype(str).str.strip() != "10"]

    # Réplica de Table.Distinct(..., {"B8_LOTECTL"}) — uma linha por lote.
    df = df.drop_duplicates(subset=["B8_LOTECTL"], keep="first")

    df["B8_DATA"] = pd.to_datetime(df["B8_DATA"], errors="coerce")
    for col in ["B8_SALDO", "B8_SALDO2"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def _quantidade(row) -> float | None:
    if row["B1_GRUPO"] == "1100":
        return row["B8_SALDO"]
    if row["B1_GRUPO"] in ("2100", "2200"):
        return row["B8_SALDO2"]
    return None  # grupo não classificado (ver aviso no topo do arquivo)


def _bucket(dias: int) -> str | None:
    if 30 <= dias < 60:
        return "30-60"
    if 60 <= dias < 90:
        return "60-90"
    if dias >= 90:
        return ">90"
    return None  # < 30 dias — não entra em nenhum cluster nomeado


def estoque_vencido() -> dict:
    df = fetch_estoque()
    hoje = pd.Timestamp(dt.date.today())

    df["dias_em_estoque"] = (hoje - df["B8_DATA"]).dt.days
    df["quantidade"] = df.apply(_quantidade, axis=1)
    df["bucket"] = df["dias_em_estoque"].apply(lambda d: _bucket(d) if pd.notna(d) else None)
    df["grupo_desc"] = df["B1_GRUPO"].map(GRUPOS)

    classificaveis = df[df["quantidade"].notna()]
    nao_classificados = df[df["quantidade"].isna()]

    buckets = {"30-60": 0.0, "60-90": 0.0, ">90": 0.0}
    for bucket, soma in classificaveis.groupby("bucket")["quantidade"].sum().items():
        if bucket in buckets:
            buckets[bucket] = float(soma)

    vencido_total = float(classificaveis.loc[classificaveis["dias_em_estoque"] >= 30, "quantidade"].sum())

    por_grupo = (
        classificaveis[classificaveis["dias_em_estoque"] >= 30]
        .groupby("grupo_desc")["quantidade"]
        .sum()
        .round(2)
        .to_dict()
    )

    return {
        "atualizado_em": dt.datetime.now().isoformat(),
        "buckets": {k: round(v, 2) for k, v in buckets.items()},
        "estoque_vencido_total": round(vencido_total, 2),
        "estoque_vencido_por_grupo": por_grupo,
        "grupos_nao_classificados": sorted(nao_classificados["B1_GRUPO"].dropna().unique().tolist()),
    }
