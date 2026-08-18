"""
Indicadores migrados do Power BI, calculados sobre os DataFrames de
VW_BASE_QUANTIDADE e VW_BASE_TEMPO — replicando as medidas DAX reais,
extraídas do arquivo DASHBOARD_LITOGRAFIA.pbix.

Validado batendo exato com o BI real (13/08/2026):
- Tempo Total, Tempo Produção, Tempo Refeição, Tempo Sem Expediente: exatos.
- % Disponibilidade Capacidade: ~63,6% calculado vs 65,68% do BI — resíduo
  de ~2pp rastreado a 7 chaves duplicadas na tabela de referência "Paradas"
  do próprio arquivo original (ambiguidade que já existe lá, não é bug
  introduzido aqui — ver categorizacao.py).

Regras confirmadas:
1. Linhas do dashboard: fixo em 8 (Envernizadeira 2, Envernizadeira 4 e
   Litografia 3 estão desativadas e ficam de fora de tudo — confirmado
   pelo Igor).
2. Categorização por coluna:
   - "Análise Gerencial" (recalculada em Python, não vem do SQL — ver
     categorizacao.py): PRODUÇÃO, REFEIÇÃO, SEM EXPEDIENTE.
   - "Análise Nova" (join com tabela Paradas): SEM PROGRAMAÇÃO, TESTE,
     MANUTENÇÃO PREVENTIVA, PC FACTORY, SETUP, EXTERNO, MANUTENÇÃO CORRETIVA.
3. "_Excesso de Set Up" é um valor AGREGADO (não linha a linha):
   max(0, Tempo Setup total − Soma de Meta Setup válidas), onde "válida"
   = Meta Setup ≠ 0 E T.Decorrido > 15 minutos (sem depender da flag
   Setup='SIM').
4. Tabela "linhas em verde" em linhas_em_verde.py.
"""
import pandas as pd

from linhas_em_verde import LINHAS_EM_VERDE, LINHA_ABREV
from categorizacao import status_da_fonte

COLUNA_RECURSO = "Apelido Recurso"

# Linhas consideradas no dashboard "Litografia" — Envernizadeira 2,
# Envernizadeira 4 e Litografia 3 estão desativadas (confirmado pelo Igor).
LINHAS_DASHBOARD = {
    "Envernizadeira 1", "Envernizadeira 3", "Envernizadeira 5", "Envernizadeira 6",
    "LITOGRAFIA 2", "LITOGRAFIA 4", "LITOGRAFIA 5", "LITOGRAFIA 6",
}

METAS = {
    "performance": 0.85,
    "disponibilidade_producao": 0.65,
    "corretiva": 0.06,
    "oee": 0.55,
}


def filtrar_linhas_dashboard(df_tempo: pd.DataFrame) -> pd.DataFrame:
    return df_tempo[df_tempo[COLUNA_RECURSO].isin(LINHAS_DASHBOARD)]


def _horas_por(df_tempo: pd.DataFrame, coluna: str, valor: str) -> float:
    return df_tempo.loc[df_tempo[coluna] == valor, "T.Decorrido (h)"].sum()


# ---------- VW_BASE_QUANTIDADE ----------
def producao_total(df_qtd: pd.DataFrame) -> float:
    return df_qtd["Quantidade Produzida"].sum() + df_qtd["Perdas"].sum()


def perc_perdas(df_qtd: pd.DataFrame) -> float:
    total = producao_total(df_qtd)
    return df_qtd["Perdas"].sum() / total if total else 0.0


def ftt(df_qtd: pd.DataFrame) -> float:
    total = producao_total(df_qtd)
    return df_qtd["Quantidade Produzida"].sum() / total if total else 0.0


# ---------- VW_BASE_TEMPO — tempos base (já filtrado pras 8 linhas) ----------
def tempo_total(df_tempo: pd.DataFrame) -> float:
    return df_tempo["T.Decorrido (h)"].sum()


def tempo_producao(df_tempo: pd.DataFrame) -> float:
    return _horas_por(df_tempo, "Análise Gerencial", "PRODUÇÃO")


def tempo_refeicao(df_tempo: pd.DataFrame) -> float:
    return _horas_por(df_tempo, "Análise Gerencial", "REFEIÇÃO")


def tempo_sem_expediente(df_tempo: pd.DataFrame) -> float:
    return _horas_por(df_tempo, "Análise Gerencial", "SEM EXPEDIENTE")


def tempo_sem_programacao(df_tempo: pd.DataFrame) -> float:
    return _horas_por(df_tempo, "Análise Nova", "SEM PROGRAMAÇÃO")


def tempo_teste(df_tempo: pd.DataFrame) -> float:
    return _horas_por(df_tempo, "Análise Nova", "TESTE")


def tempo_preventiva(df_tempo: pd.DataFrame) -> float:
    return _horas_por(df_tempo, "Análise Nova", "MANUTENÇÃO PREVENTIVA")


def tempo_pc_factory(df_tempo: pd.DataFrame) -> float:
    return _horas_por(df_tempo, "Análise Nova", "PC FACTORY")


def tempo_setup(df_tempo: pd.DataFrame) -> float:
    return _horas_por(df_tempo, "Análise Nova", "SETUP")


def tempo_externo(df_tempo: pd.DataFrame) -> float:
    return _horas_por(df_tempo, "Análise Nova", "EXTERNO")


def tempo_corretiva(df_tempo: pd.DataFrame) -> float:
    return _horas_por(df_tempo, "Análise Nova", "MANUTENÇÃO CORRETIVA")


def soma_setup_padrao(df_tempo: pd.DataFrame) -> float:
    """__Soma Set Up Padrão: soma de Meta Setup (h) onde Meta Setup <> 0
    E T.Decorrido > 15 minutos — sem depender da flag Setup='SIM'."""
    filtro = (df_tempo["Meta Setup (h)"] != 0) & (df_tempo["T.Decorrido (h)"] > 0.25)
    return df_tempo.loc[filtro, "Meta Setup (h)"].sum()


def excesso_setup(df_tempo: pd.DataFrame) -> float:
    """_Excesso de Set Up = max(0, Tempo Setup − Soma Set Up Padrão)."""
    return max(0.0, tempo_setup(df_tempo) - soma_setup_padrao(df_tempo))


def tempo_disponivel_capacidade(df_tempo: pd.DataFrame) -> float:
    return (
        tempo_total(df_tempo)
        - tempo_refeicao(df_tempo)
        - tempo_sem_expediente(df_tempo)
        - tempo_sem_programacao(df_tempo)
        - tempo_teste(df_tempo)
        - tempo_preventiva(df_tempo)
        - tempo_pc_factory(df_tempo)
        - tempo_setup(df_tempo)
        + excesso_setup(df_tempo)
        - tempo_externo(df_tempo)
    )


def disponibilidade_geral_base(df_tempo: pd.DataFrame) -> float:
    return tempo_total(df_tempo) - tempo_sem_expediente(df_tempo) - tempo_refeicao(df_tempo)


# ---------- "Linhas em verde" (produção esperada) ----------
def tempo_producao_por_recurso(df_tempo: pd.DataFrame) -> pd.Series:
    producao = df_tempo[df_tempo["Análise Gerencial"] == "PRODUÇÃO"]
    return producao.groupby(COLUNA_RECURSO)["T.Decorrido (h)"].sum()


def producao_esperada(df_tempo: pd.DataFrame) -> float:
    horas_por_linha = tempo_producao_por_recurso(df_tempo)
    total = 0.0
    for recurso, horas in horas_por_linha.items():
        velocidade = LINHAS_EM_VERDE.get(recurso)
        if velocidade is None:
            continue
        total += horas * velocidade
    return total


# ---------- Produção por linha (painel Litografia) ----------
def producao_por_linha(df_qtd: pd.DataFrame) -> dict:
    """Quantidade Produzida por linha, já filtrado pras 8 linhas ativas
    do dashboard e separado em impressoras (LITOGRAFIA) vs
    envernizadeiras (Envernizadeira), com o rótulo abreviado (ENV1,
    LITO2 etc.) usado no gráfico."""
    df = df_qtd[df_qtd["Apelido Recurso"].isin(LINHAS_DASHBOARD)]
    por_linha = df.groupby("Apelido Recurso")["Quantidade Produzida"].sum()

    impressoras, envernizadeiras = [], []
    for recurso, qtd in por_linha.items():
        item = {"linha": LINHA_ABREV.get(recurso, recurso), "quantidade": float(qtd)}
        (impressoras if recurso.startswith("LITOGRAFIA") else envernizadeiras).append(item)

    impressoras.sort(key=lambda x: -x["quantidade"])
    envernizadeiras.sort(key=lambda x: -x["quantidade"])
    return {"impressoras": impressoras, "envernizadeiras": envernizadeiras}


# ---------- Corretiva por linha (painel Manutenção) ----------
def corretiva_por_linha(df_tempo: pd.DataFrame) -> list:
    """% do tempo em manutenção corretiva por linha (Análise Nova),
    já filtrado pras 8 linhas ativas do dashboard."""
    df = filtrar_linhas_dashboard(df_tempo)
    total_por_linha = df.groupby("Apelido Recurso")["T.Decorrido (h)"].sum()
    corretiva = df[df["Análise Nova"] == "MANUTENÇÃO CORRETIVA"]
    corretiva_horas_por_linha = corretiva.groupby("Apelido Recurso")["T.Decorrido (h)"].sum()

    resultado = []
    for recurso, total in total_por_linha.items():
        horas_corretiva = corretiva_horas_por_linha.get(recurso, 0.0)
        pct = (horas_corretiva / total * 100) if total else 0.0
        resultado.append({"linha": LINHA_ABREV.get(recurso, recurso), "percentual": round(pct, 2)})

    resultado.sort(key=lambda x: -x["percentual"])
    return resultado


# ---------- Indicadores finais ----------
def performance(df_qtd: pd.DataFrame, df_tempo: pd.DataFrame) -> float:
    esperada = producao_esperada(df_tempo)
    return producao_total(df_qtd) / esperada if esperada else 0.0


def disponibilidade_producao(df_tempo: pd.DataFrame) -> float:
    disponivel = tempo_disponivel_capacidade(df_tempo)
    return tempo_producao(df_tempo) / disponivel if disponivel else 0.0


def corretiva(df_tempo: pd.DataFrame) -> float:
    base = disponibilidade_geral_base(df_tempo)
    return tempo_corretiva(df_tempo) / base if base else 0.0


def eficiencia_setup(df_tempo: pd.DataFrame):
    # AVALIAR — sem cálculo definido ainda, conforme pedido no prompt original.
    return None


def oee(df_qtd: pd.DataFrame, df_tempo: pd.DataFrame) -> float:
    return performance(df_qtd, df_tempo) * disponibilidade_producao(df_tempo) * ftt(df_qtd)


def montar_kpis(df_qtd: pd.DataFrame, df_tempo: pd.DataFrame) -> dict:
    df_tempo_dash = filtrar_linhas_dashboard(df_tempo)
    return {
        "producao_total": producao_total(df_qtd),
        "perc_perdas": perc_perdas(df_qtd),
        "performance": {"valor": performance(df_qtd, df_tempo_dash), "meta": METAS["performance"]},
        "disponibilidade_producao": {"valor": disponibilidade_producao(df_tempo_dash), "meta": METAS["disponibilidade_producao"]},
        "corretiva": {"valor": corretiva(df_tempo_dash), "meta": METAS["corretiva"]},
        "eficiencia_setup": {"valor": eficiencia_setup(df_tempo_dash), "meta": None},
        "oee": {"valor": oee(df_qtd, df_tempo_dash), "meta": METAS["oee"]},
    }


def debug_breakdown(df_qtd: pd.DataFrame, df_tempo: pd.DataFrame) -> dict:
    df_tempo_dash = filtrar_linhas_dashboard(df_tempo)
    horas_por_linha = tempo_producao_por_recurso(df_tempo_dash).to_dict()
    esperada_por_linha = {
        recurso: horas * LINHAS_EM_VERDE.get(recurso, 0)
        for recurso, horas in horas_por_linha.items() if recurso in LINHAS_EM_VERDE
    }
    linhas_excluidas = sorted(set(df_tempo[COLUNA_RECURSO].unique()) - LINHAS_DASHBOARD)
    linhas_nao_categorizadas = sorted(
        df_tempo_dash.loc[df_tempo_dash["Análise Nova"] == "CADASTRAR", "(R)Nome Detalhe"].dropna().unique()
    )
    return {
        "linhas_dashboard": sorted(LINHAS_DASHBOARD),
        "linhas_excluidas_do_calculo": linhas_excluidas,
        "fonte_paradas": status_da_fonte(),
        "detalhes_sem_categoria_analise_nova": linhas_nao_categorizadas,
        "quantidade": {
            "soma_quantidade_produzida": float(df_qtd["Quantidade Produzida"].sum()),
            "soma_perdas": float(df_qtd["Perdas"].sum()),
            "producao_total": producao_total(df_qtd),
            "ftt": ftt(df_qtd),
        },
        "tempo_horas": {
            "tempo_total": tempo_total(df_tempo_dash),
            "tempo_producao": tempo_producao(df_tempo_dash),
            "tempo_refeicao": tempo_refeicao(df_tempo_dash),
            "tempo_sem_expediente": tempo_sem_expediente(df_tempo_dash),
            "tempo_sem_programacao": tempo_sem_programacao(df_tempo_dash),
            "tempo_teste": tempo_teste(df_tempo_dash),
            "tempo_preventiva": tempo_preventiva(df_tempo_dash),
            "tempo_pc_factory": tempo_pc_factory(df_tempo_dash),
            "tempo_setup": tempo_setup(df_tempo_dash),
            "soma_setup_padrao": soma_setup_padrao(df_tempo_dash),
            "excesso_setup": excesso_setup(df_tempo_dash),
            "tempo_externo": tempo_externo(df_tempo_dash),
            "tempo_corretiva": tempo_corretiva(df_tempo_dash),
            "tempo_disponivel_capacidade": tempo_disponivel_capacidade(df_tempo_dash),
            "disponibilidade_geral_base": disponibilidade_geral_base(df_tempo_dash),
        },
        "producao_esperada": {
            "por_linha": esperada_por_linha,
            "horas_producao_por_linha": horas_por_linha,
            "total": producao_esperada(df_tempo_dash),
        },
        "indicadores_finais": montar_kpis(df_qtd, df_tempo),
    }