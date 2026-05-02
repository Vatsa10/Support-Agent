import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Config:
    # API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")

    # Postgres (Aiven)
    PG_URI = os.getenv("PG_URI", "")
    PG_SSLROOTCERT = os.getenv("PG_SSLROOTCERT", "")
    RLS_ROLE = os.getenv("RLS_ROLE", "app_user")

    # Valkey (Aiven)
    VALKEY_URI = os.getenv("VALKEY_URI", "")

    # Embeddings
    DENSE_MODEL = "models/embedding-001"
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 768))

    # Search
    TOP_K = int(os.getenv("TOP_K_RETRIEVAL", 5))
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.7))

    # Rate limit
    RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", 60))

    # App
    ENVIRONMENT = Environment(os.getenv("ENVIRONMENT", "development"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    PORT = int(os.getenv("PORT", 8000))

    # Knowledge Base (per-tenant subdir convention: <KB_PATH>/<tenant_id>/...)
    KB_PATH = os.getenv("KB_PATH", "./src/knowledge_base/")

    # LLM
    LLM_MODEL = "gemini-2.0-flash"
    LLM_TEMPERATURE = 0.7


config = Config()
