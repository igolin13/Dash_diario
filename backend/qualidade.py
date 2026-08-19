"""
Indicadores de Qualidade. Duas fontes:
- VW_RNC (schema PROTHEUS_PRD) — RNC's em aberto / RNC's no mês
- VW_ESTOQUE (mesmo schema, já usada em estoque.py) — Fardos retidos

⚠️ PONTOS NÃO CONFIRMADOS — assumidos com o melhor palpite disponível,
sinalizados aqui pra não silenciar a incerteza:

1. QI2_FNC: o Igor mencionou "se quiser usar a tabela QI2_FNC pra
   referência de contagem" — mas QI2_FNC parece, pelo padrão de nomes,
   ser uma COLUNA da própria VW_RNC (não uma tabela separada), com o
   número do FNC/RNC — provavelmente existe pra evitar contar a mesma
   RNC duas vezes se a view tiver mais de uma linha por registro (ex:
   uma linha por item/produto da mesma RNC). Por isso uso
   COUNT(DISTINCT QI2_FNC) em vez de COUNT(*). Se QI2_FNC não existir
   como coluna em VW_RNC, troque por COUNT(*) puro (ver USAR_QI2_FNC
   abaixo).

2. Fardos retidos: o Igor pediu "contar quantas OPs" com
   B8_XXSITLT='L99', mas não indicou uma coluna específica de número de
   OP dentro de VW_ESTOQUE — por ora conto linhas (COUNT(*)) que batem
   com esse filtro, sem aplicar os outros filtros de negócio que já
   existem em estoque.py (esses eram específicos pro cálculo de
   "estoque vencido"; aqui é uma pergunta diferente, então comecei sem
   eles — me avise se "fardos retidos" também deveria respeitar aquelas
   mesmas exclusões de filial/grupo/proprietário/comprador).

Todos os 3 indicadores usam a mesma conexão de estoque.py (schema
PROTHEUS_PRD).
"""
import pandas as pd
from sqlalchemy import text

from estoque import get_engine_estoque

FILIAL = "010101"
ANO = "2026"

COLUNA_DATA_RNC = "QI2_REGIST"  # confirmado pelo Igor — data de registro da RNC
USAR_QI2_FNC = True  # ⚠️ não confirmado — ver ponto (2) acima


_CONTADOR_RNC = "COUNT(DISTINCT QI2_FNC)" if USAR_QI2_FNC else "COUNT(*)"


# ---------- RNC's em aberto (aguardando resposta) ----------
_QUERY_RNC_ABERTAS = f"""
    SELECT {_CONTADOR_RNC} AS total
    FROM dbo.VW_RNC
    WHERE QI2_FILIAL = :filial
      AND CONVERT(varchar(4), QI2_ANO) = :ano
      AND QI2_STATUS_DESC IN ('Em análise', 'Registrada')
      AND QI2_SITUAC = 'Não Conformidade Existente'
      AND TIPO_RNC = 'EXTERNO'
"""


def rnc_abertas_total() -> int:
    params = {"filial": FILIAL, "ano": ANO}
    df = pd.read_sql(text(_QUERY_RNC_ABERTAS), get_engine_estoque(), params=params)
    return int(df["total"].iloc[0]) if not df.empty else 0


# ---------- RNC's no mês (todas recebidas no mês da data selecionada) ----------
_QUERY_RNC_NO_MES = f"""
    SELECT {_CONTADOR_RNC} AS total
    FROM dbo.VW_RNC
    WHERE QI2_FILIAL = :filial
      AND CONVERT(varchar(4), QI2_ANO) = :ano
      AND QI2_STATUS_DESC IN ('Em análise', 'Procede', 'Registrada')
      AND QI2_SITUAC = 'Não Conformidade Existente'
      AND TIPO_RNC = 'EXTERNO'
      AND LEFT(CONVERT(varchar(8), {COLUNA_DATA_RNC}, 112), 6) = :ano_mes
"""


def rnc_no_mes_total(data_referencia) -> int:
    """data_referencia: um date/datetime — usa o ANO+MÊS dele pra filtrar."""
    ano_mes = data_referencia.strftime("%Y%m")
    params = {"filial": FILIAL, "ano": ANO, "ano_mes": ano_mes}
    df = pd.read_sql(text(_QUERY_RNC_NO_MES), get_engine_estoque(), params=params)
    return int(df["total"].iloc[0]) if not df.empty else 0


# ---------- Fardos retidos ----------
_QUERY_FARDOS_RETIDOS = """
    SELECT COUNT(*) AS total
    FROM dbo.VW_ESTOQUE WITH (NOLOCK)
    WHERE B8_XXSITLT = 'L99'
"""


def fardos_retidos_total() -> int:
    df = pd.read_sql(text(_QUERY_FARDOS_RETIDOS), get_engine_estoque())
    return int(df["total"].iloc[0]) if not df.empty else 0


def qualidade_resumo(data_referencia) -> dict:
    return {
        "rnc_abertas": rnc_abertas_total(),
        "rnc_no_mes": rnc_no_mes_total(data_referencia),
        "fardos_retidos": fardos_retidos_total(),
        "mes_referencia": data_referencia.strftime("%Y-%m"),
    }