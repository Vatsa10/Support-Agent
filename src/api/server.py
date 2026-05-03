from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from api.admin import router as admin_router
from api.integrations import router as integrations_router
from cache.valkey import init_cache, close_cache
from config import config
from db.pool import init_pool, close_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing Support Agent SaaS...")
    await init_pool()
    print("PG pool ready.")
    await init_cache()
    print("Valkey ready.")
    yield
    print("Shutting down...")
    await close_cache()
    await close_pool()


app = FastAPI(
    title="24x7 Support Agent SaaS",
    description="Multi-tenant AI support operator (LangGraph + pgvector + Aiven)",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(admin_router, prefix="/admin")
app.include_router(integrations_router, prefix="/admin")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=config.ENVIRONMENT == "development",
    )
