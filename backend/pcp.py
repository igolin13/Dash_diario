"""
Consolidação do histórico de programação — painel de PCP.

Lê todos os CSVs exportados diariamente pelo sistema Python legado
(salvos automaticamente na pasta de rede) e consolida num único
relatório, além de calcular a aderência real (planejado congelado vs.
realizado).

Colunas confirmadas pelo Igor (com dados reais de exemplo):
  Textbox4       = máquina/linha
  ExecutionTime  = data/hora em que o ARQUIVO foi gerado (se repete em
                   todas as linhas do arquivo) — usado como referência
                   pra ordenar/selecionar arquivos, em vez da data de
                   criação no disco (mais confiável: cópia/sincronização
                   de rede pode alterar a data do arquivo, mas não o
                   conteúdo do CSV).
  OrderNo1       = identificação da OP (formato diferente do usado em
                   VW_BASE_QUANTIDADE — ver extrair_numero_op)
  SetupStart     = quando a operação está programada pra rodar (usada
                   pra saber em que dia a operação está prevista, e pra
                   detectar reprogramação)
  EndTime        = final da operação
  Quantity       = quantidade prevista
  OperationName1 = número da passada (ex: "1 PASSADA") — uma OP pode
                   ter várias passadas em dias diferentes, então o
                   casamento entre programação e produção real é feito
                   por (OP, passada), não só pela OP.

⚠️ ASSUMIDO — ainda não confirmado:
1. Delimitador/encoding: detectados automaticamente por arquivo (visto
   nos exemplos reais: vírgula + utf-8-sig na programação).
2. "Dados complementares dia a dia" na consolidação geral
   (consolidar_historico): assumo que cada exportação pode reexportar
   o histórico inteiro, por isso removo duplicatas exatas.
3. Nome dos arquivos: não sigo padrão específico, leio todo .csv da pasta.
"""
import csv
import os
import re
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
        return ";"


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


def _execution_time(df: pd.DataFrame) -> "pd.Timestamp | None":
    """Data/hora de geração do arquivo, segundo o PRÓPRIO conteúdo do
    CSV (coluna ExecutionTime, igual em todas as linhas) — mais
    confiável que a data do arquivo no disco/rede."""
    if "ExecutionTime" not in df.columns or df.empty:
        return None
    valor = pd.to_datetime(df["ExecutionTime"].iloc[0], dayfirst=True, errors="coerce")
    return valor if pd.notna(valor) else None


def listar_arquivos_brutos(pasta: str) -> list[Path]:
    caminho = Path(pasta)
    if not caminho.exists():
        raise FileNotFoundError(
            f"Pasta não encontrada ou inacessível: {pasta}. "
            f"Confere se esse PC tem acesso à rede/compartilhamento."
        )
    return list(caminho.glob("*.csv"))


def listar_arquivos(pasta: str = PASTA_HISTORICO) -> list[Path]:
    """Arquivos ordenados por data de criação no disco — usado só pela
    consolidação geral (resumo_historico), que não depende de
    ExecutionTime."""
    return sorted(listar_arquivos_brutos(pasta), key=lambda p: p.stat().st_ctime)


def _info_arquivos_programacao(pasta: str) -> list[tuple[Path, "pd.Timestamp", pd.DataFrame]]:
    """Lê cada CSV de programação, extrai o ExecutionTime real (de
    dentro do arquivo) e devolve (caminho, execution_time, dataframe)
    ordenados cronologicamente por ExecutionTime — não pela data do
    arquivo no disco."""
    resultado = []
    for caminho in listar_arquivos_brutos(pasta):
        try:
            df = _ler_csv(caminho)
            exec_time = _execution_time(df)
        except Exception:
            continue
        if exec_time is not None:
            resultado.append((caminho, exec_time, df))
    return sorted(resultado, key=lambda item: item[1])


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


# ---------- Programação "congelada" pra análise de aderência ----------
def arquivo_congelado(data_alvo, pasta: str = PASTA_HISTORICO):
    """Acha o arquivo cujo ExecutionTime (data/hora real de geração,
    lida de dentro do CSV) é o mais recente ANTES da virada pro dia
    `data_alvo`. Retorna (caminho, dataframe) ou (None, None) se não
    existir histórico suficiente."""
    import datetime as dt

    inicio_do_dia = dt.datetime.combine(data_alvo, dt.time.min)
    candidatos = [item for item in _info_arquivos_programacao(pasta) if item[1] < inicio_do_dia]
    if not candidatos:
        return None, None
    caminho, _, df = candidatos[-1]
    return caminho, df


def programacao_congelada(data_alvo, pasta: str = PASTA_HISTORICO) -> pd.DataFrame:
    """DataFrame da programação tal como estava no arquivo congelado
    pro dia `data_alvo` (ver arquivo_congelado)."""
    caminho, df = arquivo_congelado(data_alvo, pasta)
    if df is None:
        raise FileNotFoundError(
            f"Nenhum arquivo de programação encontrado antes de {data_alvo} — "
            f"sem histórico suficiente pra calcular a aderência desse dia."
        )
    return df


def extrair_numero_op(valor) -> "str | None":
    """Extrai o núcleo do número da OP, compatível com os dois formatos
    vistos: "01-22960401001" (VW_BASE_QUANTIDADE) e "01229589-33"
    (histórico de programação). Regra confirmada pelo Igor batendo com
    os dois exemplos reais: tira tudo que não é dígito, pula os 2
    primeiros dígitos (filial) e pega os 6 seguintes.
    "01-22960401001" -> "229604" | "01229589-33" -> "229589"."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    digitos = re.sub(r"[^0-9]", "", str(valor))
    return digitos[2:8] if len(digitos) >= 8 else None


def _numero_passada(valor) -> "str | None":
    """Extrai só o número da passada, ignorando a palavra que acompanha
    (que pode vir com erro de digitação — ex: "1 PASSADA" vs
    "1 PASSDAA" — ambos vistos em dados reais). "CORTE" (sem número)
    vira None, e portanto não casa com nenhuma passada numerada."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    m = re.match(r"\s*(\d+)", str(valor))
    return m.group(1) if m else None


def _parse_data_hora(serie: pd.Series) -> pd.Series:
    return pd.to_datetime(serie, dayfirst=True, errors="coerce")


def _chave_operacao(df: pd.DataFrame) -> pd.Series:
    """Chave única de uma OPERAÇÃO específica (OP + passada), não da OP
    inteira — uma mesma OP pode ter várias passadas em dias diferentes,
    e isso é normal (multi-etapa), não reprogramação."""
    passada = df["OperationName1"].apply(_numero_passada) if "OperationName1" in df.columns else None
    return df["_numero_op"].astype(str) + "|" + passada.astype(str)


def programacao_do_dia(data_alvo, pasta: str = PASTA_HISTORICO) -> pd.DataFrame:
    """Linhas do arquivo congelado cuja SetupStart cai no dia
    `data_alvo` — o arquivo congelado cobre vários dias pra frente,
    essa função filtra só o dia que interessa."""
    df = programacao_congelada(data_alvo, pasta).copy()
    df["_setup_start_dt"] = _parse_data_hora(df["SetupStart"])
    df["_numero_op"] = df["OrderNo1"].apply(extrair_numero_op)
    df["_passada"] = df["OperationName1"].apply(_numero_passada)
    df["_chave_operacao"] = _chave_operacao(df)
    return df[df["_setup_start_dt"].dt.date == data_alvo].reset_index(drop=True)


def verificar_reprogramacao(data_alvo, pasta: str = PASTA_HISTORICO) -> pd.DataFrame:
    """Pra cada OPERAÇÃO planejada pro dia `data_alvo` (OP + passada,
    segundo o arquivo congelado), verifica se ela CONTINUA aparecendo
    programada especificamente pra `data_alvo` em algum arquivo gerado
    DEPOIS do congelado (por ExecutionTime, não data de disco). Só é
    considerada reprogramada se, em NENHUM arquivo posterior, ela mais
    aparecer com SetupStart em `data_alvo` — ou seja, avaliamos se ela
    vai rodar NAQUELE DIA especificamente, não a programação inteira
    (uma OP pode aparecer de novo em dias futuros na agenda, isso não
    conta como reprogramação da instância do dia analisado). Compara
    por operação específica (OP+passada), não pela OP inteira, pra não
    confundir "reprogramação" com "a OP tem outra passada em outro dia"
    (normal). Adiciona as colunas "_reprogramada" (booleana) e
    "_nova_data" (pra onde foi reprogramada, ou None)."""
    planejado = programacao_do_dia(data_alvo, pasta)
    if planejado.empty:
        planejado["_reprogramada"] = pd.Series(dtype=bool)
        planejado["_nova_data"] = pd.Series(dtype=object)
        return planejado

    caminho_base, _ = arquivo_congelado(data_alvo, pasta)
    todos = _info_arquivos_programacao(pasta)
    exec_time_base = next(item[1] for item in todos if item[0] == caminho_base)
    posteriores = [item for item in todos if item[1] > exec_time_base]

    confirmada_no_dia = set()  # chaves que CONTINUAM aparecendo em data_alvo em algum posterior
    ultima_data_vista = {}  # chave -> data mais recente vista (só usado se NÃO confirmada no dia)
    for _, _, df in posteriores:
        df = df.copy()
        df["_numero_op"] = df["OrderNo1"].apply(extrair_numero_op)
        df["_chave_operacao"] = _chave_operacao(df)
        df["_setup_start_dt"] = _parse_data_hora(df["SetupStart"])

        no_dia = df[df["_setup_start_dt"].dt.date == data_alvo]
        confirmada_no_dia.update(no_dia["_chave_operacao"].unique())

        for chave, grupo in df.groupby("_chave_operacao"):
            data_max = grupo["_setup_start_dt"].max()
            if pd.notna(data_max):
                ultima_data_vista[chave] = data_max

    def nova_data(chave):
        if chave in confirmada_no_dia:
            return None  # ainda roda no dia analisado em pelo menos um arquivo posterior — não reprogramada
        vista_depois = ultima_data_vista.get(chave)
        if vista_depois is None:
            return None  # não reapareceu em nenhum arquivo posterior — sem indício de reprogramação
        return vista_depois.date() if vista_depois.date() != data_alvo else None

    planejado = planejado.copy()
    planejado["_nova_data"] = planejado["_chave_operacao"].apply(nova_data)
    planejado["_reprogramada"] = planejado["_nova_data"].notna()
    return planejado


def aderencia_diaria(data_alvo, pasta: str = PASTA_HISTORICO) -> dict:
    """Aderência real do dia `data_alvo`: cruza o que estava programado
    no arquivo congelado (excluindo operações reprogramadas depois) com
    o que realmente rodou, via VW_BASE_QUANTIDADE — casando por
    (OP, passada), não só pela OP."""
    from database import fetch_base_quantidade

    planejado = verificar_reprogramacao(data_alvo, pasta)
    if planejado.empty:
        return {
            "data": data_alvo.isoformat(),
            "erro": "Sem programação encontrada pra esse dia (confira se existe arquivo congelado anterior a ele).",
        }

    nao_reprogramadas = planejado[~planejado["_reprogramada"]].copy()
    nao_reprogramadas["Quantity"] = pd.to_numeric(nao_reprogramadas["Quantity"], errors="coerce").fillna(0)
    planejado_agrupado = nao_reprogramadas.groupby(["_numero_op", "_passada"])["Quantity"].sum()

    df_real = fetch_base_quantidade(data_alvo, data_alvo)
    df_real["_numero_op"] = df_real["Cód. da Ordem"].apply(extrair_numero_op)
    df_real["_passada"] = df_real["Operação"].apply(_numero_passada)
    df_real["Quantidade Produzida"] = pd.to_numeric(df_real["Quantidade Produzida"], errors="coerce").fillna(0)
    realizado_agrupado = df_real.groupby(["_numero_op", "_passada"])["Quantidade Produzida"].sum()

    detalhe = []
    for (numero_op, passada), qtd_planejada in planejado_agrupado.items():
        qtd_realizada = float(realizado_agrupado.get((numero_op, passada), 0.0))
        detalhe.append({
            "numero_op": numero_op,
            "passada": passada,
            "quantidade_planejada": float(qtd_planejada),
            "quantidade_realizada": qtd_realizada,
            "aderencia": (qtd_realizada / qtd_planejada) if qtd_planejada else None,
            "rodou": qtd_realizada > 0,
        })

    qtd_planejada_total = float(planejado_agrupado.sum())
    qtd_realizada_total = float(sum(d["quantidade_realizada"] for d in detalhe))

    reprogramadas = planejado[planejado["_reprogramada"]].copy()
    operacoes_reprogramadas = [
        {
            "numero_op": row["_numero_op"],
            "passada": row["_passada"],
            "maquina": row.get("Textbox4"),
            "data_original": data_alvo.isoformat(),
            "nova_data": row["_nova_data"].isoformat() if pd.notna(row["_nova_data"]) else None,
        }
        for _, row in reprogramadas.iterrows()
    ]

    # Contagens por OP ÚNICA (não por operação/passada) — uma OP com
    # várias passadas reprogramadas conta como 1 OP reprogramada, não
    # várias. É isso que aparece no resumo pro usuário.
    ops_unicas_planejadas = set(planejado["_numero_op"])
    ops_unicas_reprogramadas = set(reprogramadas["_numero_op"])
    ops_unicas_que_rodaram = set(d["numero_op"] for d in detalhe if d["rodou"])

    return {
        "data": data_alvo.isoformat(),
        "total_ops_planejadas": len(ops_unicas_planejadas),
        "total_ops_reprogramadas": len(ops_unicas_reprogramadas),
        "total_ops_nao_reprogramadas": len(ops_unicas_planejadas - ops_unicas_reprogramadas),
        "ops_que_rodaram": len(ops_unicas_que_rodaram),
        "quantidade_planejada_total": qtd_planejada_total,
        "quantidade_realizada_total": qtd_realizada_total,
        "aderencia_quantidade": (qtd_realizada_total / qtd_planejada_total) if qtd_planejada_total else None,
        "detalhe_por_op": detalhe,
        "operacoes_reprogramadas": operacoes_reprogramadas,
    }


# ---------- Resumo em texto via IA local (Ollama) ----------
# Importante: a IA NÃO calcula nada — só narra os números que
# aderencia_diaria() já calculou com exatidão. Ela nunca decide o valor
# da aderência, só descreve.
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://10.152.7.224:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
OLLAMA_TIMEOUT_SEGUNDOS = 30


def _montar_prompt_resumo(dados: dict) -> str:
    pct = dados.get("aderencia_quantidade")
    pct_str = f"{pct * 100:.1f}%" if pct is not None else "indisponível"
    piores = sorted(
        (d for d in dados.get("detalhe_por_op", []) if d.get("aderencia") is not None),
        key=lambda d: d["aderencia"],
    )[:2]
    piores_txt = "; ".join(f"OP {d['numero_op']} passada {d['passada']} ({d['aderencia'] * 100:.0f}%)" for d in piores) or "nenhuma"

    reprog = dados.get("operacoes_reprogramadas", [])[:3]
    reprog_txt = "; ".join(
        f"OP {r['numero_op']} passada {r['passada']} (de {r['data_original']} para {r['nova_data']})"
        for r in reprog
    ) or "nenhuma"

    return f"""Você é um analista de PCP industrial. Resuma a aderência de produção do dia {dados['data']} em português do Brasil, em formato de TÓPICOS curtos (bullet points), objetivo e direto — nada de introdução ou conclusão, só os pontos principais. Máximo 4 tópicos, cada um com no máximo 1 frase curta.

Dados (não invente nenhum número fora destes):
- OPs planejadas: {dados['total_ops_planejadas']}
- OPs reprogramadas depois do planejamento (excluídas do cálculo): {dados['total_ops_reprogramadas']}
- Exemplos de reprogramação: {reprog_txt}
- OPs que efetivamente rodaram: {dados['ops_que_rodaram']} de {dados['total_ops_nao_reprogramadas']}
- Quantidade planejada total: {dados['quantidade_planejada_total']:.0f}
- Quantidade realizada total: {dados['quantidade_realizada_total']:.0f}
- Aderência de quantidade: {pct_str}
- OPs com pior aderência: {piores_txt}

Cubra: nível geral de aderência, volume de reprogramações (cite destino se relevante), e a pior OP se houver alguma crítica."""


def gerar_resumo_ia(dados: dict) -> str:
    import requests

    prompt = _montar_prompt_resumo(dados)
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=OLLAMA_TIMEOUT_SEGUNDOS,
        )
        resp.raise_for_status()
        texto = resp.json().get("response", "").strip()
        if not texto:
            raise RuntimeError("A IA respondeu vazio")
        return texto
    except requests.RequestException as erro:
        raise RuntimeError(f"Não consegui falar com a IA local ({OLLAMA_URL}): {erro}")