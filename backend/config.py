"""
Configuração de conexão com o SQL Server (schema PCF4_PRD).

Os valores abaixo vêm do "Prompt dos deuses". Em produção, mova-os para
variáveis de ambiente (.env) — nunca deixe usuário/senha hardcoded em
código versionado. Por ora, os defaults abaixo permitem rodar local.
"""
import os

DB_CONFIG = {
    "host": os.getenv("DASH_DB_HOST", "srvdb-01"),
    "port": int(os.getenv("DASH_DB_PORT", "1433")),
    "schema": os.getenv("DASH_DB_SCHEMA", "PCF4_PRD"),
    "user": os.getenv("DASH_DB_USER", "consult"),
    "password": os.getenv("DASH_DB_PASS", "consult"),
    "driver": os.getenv("DASH_DB_DRIVER", "ODBC Driver 18 for SQL Server"),
}

VIEW_QUANTIDADE = "VW_BASE_QUANTIDADE"
VIEW_TEMPO = "VW_BASE_TEMPO"


def build_connection_string() -> str:
    c = DB_CONFIG
    return (
        f"mssql+pyodbc://{c['user']}:{c['password']}@{c['host']}:{c['port']}/"
        f"{c['schema']}?driver={c['driver'].replace(' ', '+')}"
        f"&TrustServerCertificate=yes"
    )