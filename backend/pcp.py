"""
Consolidação do histórico de programação — painel de PCP.

Lê todos os CSVs exportados diariamente pelo sistema Python legado
(salvos automaticamente na pasta de rede) e consolida num único
relatório, num único DataFrame.

⚠️ ASSUMIDO — não confirmado com uma amostra real dos arquivos:

1. Delimitador e encoding: tento detectar automaticamente (';' ou ',',
   testando utf-8-sig / cp1252 / latin1 nessa ordem). Sistemas
   brasileiros legados costumam exportar CSV com ';' e cp1252/latin1
   (por causa de acentos), então esses são os padrões mais prováveis.

2. "Dados complementares dia a dia": assumi que cada exportação pode
   reexportar o histórico inteiro (não só as linhas novas daquele
   dia) — por isso removo linhas EXATAMENTE duplicadas ao consolidar
   (REMOVER_DUPLICATAS = True). Se cada arquivo tiver só as linhas
   novas, sem sobreposição com os dias anteriores, desativa essa
   constante que a consolidação vira um append puro.

3. Nome dos arquivos: não sigo nenhum padrão específico (tipo data no
   nome) — leio todos os .csv que existirem na pasta, sem filtrar.

4. Data de criação: cada linha ganha uma coluna "_data_arquivo" com a
   data de criação do ARQUIVO no disco (não uma data de dentro do CSV
   — assumindo que não existe uma coluna de data confiável linha a
   linha, já que o pedido foi "saber o dia da criação de cada um").
   ⚠️ Isso usa Path.stat().st_ctime, que só significa "data de criação"
   no WINDOWS (no Linux seria outra coisa — data de alteração de
   metadado). Como o backend roda em Windows, está OK.

Se algum desses pontos estiver errado, me diga que ajusto — mais fácil
corrigir agora do que descobrir na hora que o relatório vier torto.
"""
import csv
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

PASTA_HISTORICO = os.getenv(
    "PCP_PASTA_HISTORICO",
    r"\\10.147.70.8\Users\Public\Documents\Historico programação",
)
REMOVER_DUPLICATAS = True


def _detectar_delimitador(caminho: Path) -> str:
    with open(caminho, "r", encoding="utf-8-sig", errors="ignore") as f:
        amostra = f.read(4096)
    try:
        return csv.Sniffer().sniff(amostra, delimiters=";,").delimiter
    except csv.Error:
        return ";"  # padrão mais comum em sistemas brasileiros, usado como fallback


def _ler_csv(caminho: Path) -> pd.DataFrame:
    delimitador = _detectar_delimitador(caminho)
    data_criacao = datetime.fromtimestamp(caminho.stat().st_ctime)
    ultimo_erro = None
    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        try:
            df = pd.read_csv(caminho, sep=delimitador, encoding=encoding, dtype=str)
            df["_data_arquivo"] = data_criacao.strftime("%Y-%m-%d %H:%M:%S")
            return df
        except UnicodeDecodeError as erro:
            ultimo_erro = erro
            continue
    raise ValueError(
        f"Não consegui ler {caminho.name} com nenhum encoding tentado "
        f"(utf-8-sig, cp1252, latin1). Último erro: {ultimo_erro}"
    )


def listar_arquivos(pasta: str = PASTA_HISTORICO) -> list[Path]:
    caminho = Path(pasta)
    if not caminho.exists():
        raise FileNotFoundError(
            f"Pasta não encontrada ou inacessível: {pasta}. "
            f"Confere se esse PC tem acesso à rede/compartilhamento."
        )
    # Ordena por data de criação (não por nome) — garante que, ao remover
    # duplicatas, a data mantida seja sempre a mais antiga (a "primeira
    # vez" que aquela linha apareceu).
    return sorted(caminho.glob("*.csv"), key=lambda p: p.stat().st_ctime)


def consolidar_historico(pasta: str = PASTA_HISTORICO) -> pd.DataFrame:
    """Lê todos os CSVs da pasta e devolve um único DataFrame consolidado."""
    arquivos = listar_arquivos(pasta)
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo .csv encontrado em {pasta}")

    partes = []
    erros = []
    for arquivo in arquivos:
        try:
            df = _ler_csv(arquivo)
            df["_arquivo_origem"] = arquivo.name
            partes.append(df)
        except Exception as erro:
            erros.append(f"{arquivo.name}: {erro}")

    if not partes:
        raise ValueError("Nenhum dos arquivos pôde ser lido. Erros:\n" + "\n".join(erros))

    consolidado = pd.concat(partes, ignore_index=True)

    if REMOVER_DUPLICATAS:
        colunas_dedup = [c for c in consolidado.columns if c not in ("_arquivo_origem", "_data_arquivo")]
        consolidado = consolidado.drop_duplicates(subset=colunas_dedup, keep="first")

    if erros:
        print(f"[pcp] {len(erros)} arquivo(s) não puderam ser lidos e foram ignorados:")
        for e in erros:
            print(f"  - {e}")

    return consolidado.reset_index(drop=True)


def resumo_historico(pasta: str = PASTA_HISTORICO) -> dict:
    df = consolidar_historico(pasta)
    return {
        "total_linhas": int(len(df)),
        "total_arquivos": len(listar_arquivos(pasta)),
        "colunas": df.columns.tolist(),
        "dados": df.to_dict(orient="records"),
    }   