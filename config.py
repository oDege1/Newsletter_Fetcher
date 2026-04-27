# ============================================================
# Configurações do Newsletter Fetcher
# ============================================================

import os

# Pasta raiz do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Arquivo de credenciais OAuth do Google Cloud Console
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")

# Token de acesso gerado automaticamente após o primeiro login
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

# Pasta de saída para as newsletters salvas
OUTPUT_DIR = os.path.join(BASE_DIR, "newsletters_hoje")

# Formato de saída: "txt", "pdf" ou "ambos"
OUTPUT_FORMAT = "ambos"

# ============================================================
# Filtros para identificar newsletters
# ============================================================

# Remetentes específicos de newsletters (adicione os seus aqui)
# Exemplo: ["newsletter@exemplo.com", "digest@site.com"]
NEWSLETTER_SENDERS = []

# Palavras-chave no assunto do email que indicam newsletters
NEWSLETTER_KEYWORDS = [
    "newsletter",
    "digest",
    "daily",
    "semanal",
    "resumo",
    "briefing",
    "news",
    "boletim",
    "update",
    "informativo",
]

# Se True, busca TODOS os emails de hoje (ignora filtros acima)
FETCH_ALL_TODAY = False

# Número máximo de emails para buscar
MAX_RESULTS = 50
