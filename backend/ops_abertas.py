"""
Indicador de OP's em aberto — pertence ao painel de Estoque. Schema
PROTHEUS_PRD, view VW_REL_OP (mesma conexão usada por VW_ESTOQUE, ver
estoque.py).

Filtros aplicados (confirmados pelo Igor):
1. [Status] IN ('iniciada', 'ociosa')
2. [C2_FILIAL] = '010101'
3. [NUM_OP] termina em '01' (== "PA" — não existe coluna própria pra
   isso, o sufixo do número já indica)
4. [C2_EMISSAO] só de 2026
5. Só entra se hoje já passou >= 5 dias de [DT.PREVISTA] (data prevista
   de entrega)

Nomes de coluna confirmados pelo Igor com print direto do SQL Server
Management Studio (a view expõe os nomes BRUTOS do Protheus, não os
apelidos "amigáveis" que uma query anterior criava): status (minúsculo
— o banco tem collation sensível a maiúsculas/minúsculas, "Status" com
S maiúsculo dava erro de coluna inválida), C2_TPOP, C2_DATPRI,
C2_FILIAL, NUM_OP, C2_PRODUTO, B1_DESC, C2_EMISSAO, [DT.PREVISTA] (com
ponto no nome mesmo), [DT.REAL], C2_QUANT, C2_QUJE,
[SALDO A ENTREGAR], C2_QTSEGUM, C2_XXPROPR, PROP, C2_XXCOMPR,
COMPRADOR, C2_XXDESTI, DESTINATARIO, C2_XXCICLO, C2_XXCODAR,
C2_XXDCRQL, C2_DIASOCI, C2_XXPEDC, C2_XXITPED.

Tratamento de data: sem assumir se as colunas de data vêm como texto
'YYYYMMDD' ou DATE/DATETIME nativo — converte pra varchar primeiro
(funciona nos dois casos) e usa TRY_CONVERT (não quebra a query se
algum valor vier mal formatado).

Como usa GETDATE() (contagem de dias em atraso), esse indicador é
sempre "agora" — não recebe data_inicio/data_fim, igual o resto do
painel de Estoque.
"""
import pandas as pd
from sqlalchemy import text

from estoque import get_engine_estoque

DIAS_MINIMOS_ATRASO = 5
FILIAL = "010101"
ANO_EMISSAO = "2026"

# alias amigável -> expressão/coluna real na view
COLUNAS = {
    "Status": "status",
    "Tp. Producao": "C2_TPOP",
    "Previsao Ini": "C2_DATPRI",
    "Filial": "C2_FILIAL",
    "Numero da OP": "NUM_OP",
    "Produto": "C2_PRODUTO",
    "Descricao": "B1_DESC",
    "DT Emissao": "C2_EMISSAO",
    "Entrega": "[DT.PREVISTA]",
    "DT Real Fim": "[DT.REAL]",
    "Quantidade": "C2_QUANT",
    "Qtd Produzida": "C2_QUJE",
    "Saldo a Entregar": "[SALDO A ENTREGAR]",
    "Qtd 2a UM": "C2_QTSEGUM",
    "Cod Proprietario": "C2_XXPROPR",
    "Proprietario": "PROP",
    "Cod Comprador": "C2_XXCOMPR",
    "Comprador": "COMPRADOR",
    "Cod Destinatario": "C2_XXDESTI",
    "Destinatario": "DESTINATARIO",
    "Ciclo": "C2_XXCICLO",
    "Cod Ar": "C2_XXCODAR",
    "Documento CRQL": "C2_XXDCRQL",
    "Dias Ocios": "C2_DIASOCI",
    "Pedido Compra": "C2_XXPEDC",
    "Item Pedido": "C2_XXITPED",
}

_SELECT_LIST = ", ".join(f"{col} AS [{alias}]" for alias, col in COLUNAS.items())

_QUERY = f"""
    SELECT
        {_SELECT_LIST},
        DATEDIFF(
            DAY,
            TRY_CONVERT(date, NULLIF(CONVERT(varchar(20), [DT.PREVISTA], 112), ''), 112),
            GETDATE()
        ) AS [Dias Atraso]
    FROM dbo.VW_REL_OP
    WHERE status IN ('iniciada', 'ociosa')
      AND C2_FILIAL = :filial
      AND RIGHT(NUM_OP, 2) = '01'
      AND LEFT(CONVERT(varchar(20), C2_EMISSAO, 112), 4) = :ano_emissao
      AND DATEDIFF(
            DAY,
            TRY_CONVERT(date, NULLIF(CONVERT(varchar(20), [DT.PREVISTA], 112), ''), 112),
            GETDATE()
          ) >= :dias_minimos
"""


def fetch_ops_abertas() -> pd.DataFrame:
    params = {"filial": FILIAL, "ano_emissao": ANO_EMISSAO, "dias_minimos": DIAS_MINIMOS_ATRASO}
    return pd.read_sql(text(_QUERY), get_engine_estoque(), params=params)


def ops_abertas_resumo() -> dict:
    df = fetch_ops_abertas()

    lista = df[
        ["Numero da OP", "Status", "Produto", "Descricao", "Entrega", "Dias Atraso", "Proprietario", "Comprador"]
    ].to_dict(orient="records")

    por_status = df["Status"].value_counts().to_dict()

    return {
        "total": int(len(df)),
        "por_status": {k: int(v) for k, v in por_status.items()},
        "dias_minimos_atraso": DIAS_MINIMOS_ATRASO,
        "ops": lista,
    }
