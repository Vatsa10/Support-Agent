from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.routes import router
from config import config
from vector_db.ingestion import load_knowledge_base
from vector_db.retrieval import retriever

# Startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Initializing Support Agent...")
    
    # Load knowledge base
    print("📚 Loading knowledge base...")
    chunks = load_knowledge_base(config.KB_PATH)
    
    # Index documents
    print("🔍 Indexing documents...")
    retriever.index_documents(chunks)
    
    print("✅ Support Agent ready!")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")

# Create app
app = FastAPI(
    title="24x7 Support Agent",
    description="AI-powered support agent with LangGraph + Qdrant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=config.ENVIRONMENT == "development"
    )
