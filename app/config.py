import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Configurações do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/finance.db")

# Caminho do PDF
PDF_PATH = os.getenv(
    "PDF_PATH", 
    str(BASE_DIR / "data" / "magazine_luiza_itr_1t22.pdf")
)

# Configurações da API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_DEBUG = os.getenv("API_DEBUG", "True").lower() == "true"

# Configurações da Grok (xAI)
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-beta")

# Configurações de extração
MAX_TABLES_PER_EXTRACTOR = int(os.getenv("MAX_TABLES_PER_EXTRACTOR", "50"))
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "30.0"))

# Configurações do RAG
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
EMBEDDING_USE_SIMPLE = os.getenv("EMBEDDING_USE_SIMPLE", "True").lower() == "true"

# Pastas
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Cria pastas se não existirem
DATA_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Configurações de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")