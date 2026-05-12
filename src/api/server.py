from contextlib import asynccontextmanager

from db._dns_patch import install as _install_dns_fallback
_install_dns_fallback()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.admin import router as admin_router
from api.auth_routes import router as auth_router
from api.integrations import router as integrations_router
from api.public_routes import router as public_chat_router, tenant_router as pubkey_tenant_router
from api.routes import router as api_router
from api.tenant_api import router as tenant_router
from api.webhooks import router as webhooks_router
from cache.valkey import close_cache, get_client, init_cache
from config import config
from db.pool import close_pool, init_pool, sys_conn
from observability import (
    RequestIdMiddleware,
    metrics_response,
    setup_logging,
)
from observability.logging import get_logger
from scheduler import start_scheduler, stop_scheduler

setup_logging()
log = get_logger("server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup")
    await init_pool()
    await init_cache()
    start_scheduler()
    yield
    log.info("shutdown")
    stop_scheduler()
    await close_cache()
    await close_pool()


app = FastAPI(
    title="24x7 Support Agent SaaS",
    description="Multi-tenant AI support operator (LangGraph + pgvector + Aiven)",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/auth")
app.include_router(admin_router, prefix="/admin")
app.include_router(integrations_router, prefix="/admin")
app.include_router(tenant_router, prefix="/tenant")
app.include_router(pubkey_tenant_router, prefix="/tenant")
app.include_router(public_chat_router, prefix="/public")
app.include_router(webhooks_router)  # /webhooks/{tenant_id}/{kind}


@app.get("/healthz")
async def healthz():
    pg_ok = False
    valkey_ok = False
    try:
        async with sys_conn() as conn:
            await conn.fetchval("SELECT 1")
        pg_ok = True
    except Exception as e:
        log.warning("healthz_pg_fail", extra={"err": str(e)})
    try:
        pong = await get_client().ping()
        valkey_ok = bool(pong)
    except Exception as e:
        log.warning("healthz_valkey_fail", extra={"err": str(e)})

    status = "ok" if (pg_ok and valkey_ok) else "degraded"
    body = {"status": status, "pg": pg_ok, "valkey": valkey_ok}
    if status != "ok":
        from fastapi.responses import JSONResponse
        return JSONResponse(body, status_code=503)
    return body


@app.get("/metrics")
async def metrics():
    return metrics_response()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=config.ENVIRONMENT == "development",
    )
