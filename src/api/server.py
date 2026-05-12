import os
from contextlib import asynccontextmanager

from db._dns_patch import install as _install_dns_fallback
_install_dns_fallback()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from api.admin import router as admin_router
from api.auth_routes import router as auth_router
from api.billing_routes import router as billing_router
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
from observability.sentry import init_sentry
from scheduler import start_scheduler, stop_scheduler

setup_logging()
init_sentry()
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


# Two CORS surfaces:
#  - /public/* + /webhooks/* + /healthz + /metrics  → any origin (browser embed widget, vendor servers)
#  - /tenant/* + /admin/* + /auth/* + /api/*        → DASHBOARD_ORIGIN only (config-allow-list)
DASHBOARD_ORIGINS = [
    o.strip()
    for o in os.getenv("DASHBOARD_ORIGIN", "http://localhost:3000").split(",")
    if o.strip()
]
OPEN_PREFIXES = ("/public/", "/webhooks/", "/healthz", "/metrics")


class ScopedCORSMiddleware(BaseHTTPMiddleware):
    """Origin allow-list for protected routes. Open routes use permissive CORSMiddleware below."""

    async def dispatch(self, request, call_next):
        path = request.url.path
        if path.startswith(OPEN_PREFIXES):
            return await call_next(request)

        origin = request.headers.get("origin")
        # No origin header (curl, server-to-server): allow.
        if origin and origin not in DASHBOARD_ORIGINS:
            if request.method == "OPTIONS":
                return JSONResponse({"detail": "origin not allowed"}, status_code=403)
            return JSONResponse({"detail": "origin not allowed"}, status_code=403)

        resp = await call_next(request)
        if origin and origin in DASHBOARD_ORIGINS:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS,PATCH"
            resp.headers["Access-Control-Allow-Headers"] = "Authorization,Content-Type,X-API-Key,X-Admin-Key,X-End-User-JWT,X-Request-ID"
            resp.headers["Vary"] = "Origin"
        return resp


app.add_middleware(ScopedCORSMiddleware)

# Permissive CORS only for the open prefixes (public chat + webhooks).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
app.include_router(billing_router, prefix="/billing")
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
