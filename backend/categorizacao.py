"""
Reclassificação de status de parada, replicando exatamente a lógica do
Power Query do arquivo DASHBOARD_LITOGRAFIA.pbix.

"Análise Gerencial" é calculada aqui em Python (não vem do SQL — a coluna
que existe no banco está desatualizada; o Power BI ignora ela e recalcula
do zero a partir de "Nome Status Recurso").

"Análise Nova" vem de um LEFT JOIN com a planilha Google Sheets "Paradas"
(chave: "(R)Nome Detalhe" = "Detalhe de status"), a mesma que alimenta o
Power BI — buscada AO VIVO, com cache em memória (padrão: 10 min) pra não
bater no Google a cada request. Se a planilha estiver fora do ar ou sem
internet, cai automaticamente pro snapshot local (paradas_lookup.json).
"""
import json
import time
from pathlib import Path

import pandas as pd

# Planilha: https://docs.google.com/spreadsheets/d/11IgFBtonqvPy-idK9Wnk56Z-FTWRcn1ORYyjU37-Pg0
PARADAS_SHEET_ID = "11IgFBtonqvPy-idK9Wnk56Z-FTWRcn1ORYyjU37-Pg0"
PARADAS_SHEET_GID = "0"
PARADAS_SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{PARADAS_SHEET_ID}/export?format=csv&gid={PARADAS_SHEET_GID}"
)

_FALLBACK_PATH = Path(__file__).parent / "paradas_lookup.json"
_CACHE_TTL_SEGUNDOS = 600  # 10 minutos

_cache = {"dados": None, "buscado_em": 0.0, "fonte": None}


def _carregar_fallback() -> dict:
    with open(_FALLBACK_PATH, encoding="utf-8") as f:
        registros = json.load(f)
    return {r["Detalhe de status"]: r["Análise"] for r in registros}


def _buscar_da_planilha() -> dict:
    df = pd.read_csv(PARADAS_SHEET_CSV_URL)
    df = df.dropna(subset=["Detalhe de status"])
    df = df.drop_duplicates(subset=["Detalhe de status"], keep="last")
    return dict(zip(df["Detalhe de status"], df["Análise"]))


def _get_paradas(forcar_atualizacao: bool = False) -> dict:
    agora = time.time()
    cache_valido = _cache["dados"] is not None and (agora - _cache["buscado_em"]) < _CACHE_TTL_SEGUNDOS
    if cache_valido and not forcar_atualizacao:
        return _cache["dados"]

    try:
        dados = _buscar_da_planilha()
        _cache.update(dados=dados, buscado_em=agora, fonte="google_sheets")
    except Exception as erro:
        if _cache["dados"] is not None:
            # já tem algo em cache (mesmo vencido) — melhor usar isso
            # do que travar a API por causa de uma falha de rede pontual.
            print(f"[categorizacao] Falha ao atualizar planilha Paradas ({erro}); mantendo cache anterior.")
            return _cache["dados"]
        print(f"[categorizacao] Falha ao buscar planilha Paradas ({erro}); usando snapshot local.")
        dados = _carregar_fallback()
        _cache.update(dados=dados, buscado_em=agora, fonte="fallback_local")

    return _cache["dados"]


def status_da_fonte() -> dict:
    """Útil para debug: de onde vieram os dados de categorização agora."""
    return {"fonte": _cache["fonte"], "buscado_em": _cache["buscado_em"], "total_paradas": len(_cache["dados"] or {})}


def analise_gerencial(nome_status_recurso: str, nome_detalhe: str) -> str:
    """Tradução exata do step 'Personalização Adicionada' do Power Query."""
    if nome_status_recurso in ("MANUTENÇÃO ELÉTRICA", "MANUTENÇÃO MECÂNICA"):
        return "MANUTENÇÃO CORRETIVA"
    if nome_status_recurso in (
        "MANUTENÇÃO PREVENTIVA", "SEM EXPEDIENTE", "SEM PROGRAMAÇÃO", "PRODUÇÃO", "REFEIÇÃO",
    ):
        return nome_status_recurso
    if nome_status_recurso in ("SET UP (ENV)", "SET UP (LITO)"):
        return "SETUP"
    if nome_detalhe == "SETUP FORA DA PROGRAMACAO":
        return "SETUP"
    return "OUTRAS PARADAS"


def analise_nova(nome_detalhe: str) -> str:
    """LEFT JOIN com a planilha Paradas (ao vivo, com cache) via (R)Nome Detalhe."""
    paradas = _get_paradas()
    return paradas.get(nome_detalhe, "CADASTRAR")