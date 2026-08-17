"""
Tabela "linhas em verde", migrada do Power BI (confirmada pelo Igor).

Chave = "Apelido Recurso" exatamente como vem em VW_BASE_TEMPO/
VW_BASE_QUANTIDADE, pra permitir merge direto sem trocar nomes de coluna.
"""

LINHAS_EM_VERDE = {
    "Envernizadeira 1": 4700,
    "Envernizadeira 2": 3300,
    "Envernizadeira 3": 4700,
    "Envernizadeira 4": 3300,
    "Envernizadeira 5": 5700,
    "Envernizadeira 6": 4700,
    "LITOGRAFIA 2": 4200,
    "LITOGRAFIA 3": 3000,
    "LITOGRAFIA 4": 4200,
    "LITOGRAFIA 5": 4200,
    "LITOGRAFIA 6": 4200,
}

VELOCIDADE_PADRAO = {
    "Envernizadeira 1": 5000,
    "Envernizadeira 2": 3300,
    "Envernizadeira 3": 5000,
    "Envernizadeira 4": 4700,
    "Envernizadeira 5": 6000,
    "Envernizadeira 6": 5000,
    "LITOGRAFIA 2": 5000,
    "LITOGRAFIA 3": 3000,
    "LITOGRAFIA 4": 4500,
    "LITOGRAFIA 5": 4500,
    "LITOGRAFIA 6": 4500,
}
