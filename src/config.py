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
    
    # Qdrant
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    
    # Collections
    DENSE_COLLECTION = "support_agent_dense"
    SPARSE_COLLECTION = "support_agent_sparse"
    
    # Embeddings
    DENSE_MODEL = "models/embedding-001"  # Google's dense embedding model
    DENSE_DIM = 768
    
    # Search
    TOP_K = int(os.getenv("TOP_K_RETRIEVAL", 5))
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.7))
    
    # App
    ENVIRONMENT = Environment(os.getenv("ENVIRONMENT", "development"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    PORT = int(os.getenv("PORT", 8000))
    
    # Knowledge Base
    KB_PATH = os.getenv("KB_PATH", "./knowledge_base/")
    
    # LLM
    LLM_MODEL = "gemini-2.0-flash"
    LLM_TEMPERATURE = 0.7

config = Config()
