import ssl
from contextlib import asynccontextmanager
from typing import Optional
import asyncpg
from pgvector.asyncpg import register_vector

from config import config

_pool: Optional[asyncpg.Pool] = None


def _ssl_context() -> Optional[ssl.SSLContext]:
    if not config.PG_SSLROOTCERT:
        return None
    ctx = ssl.create_default_context(cafile=config.PG_SSLROOTCERT)
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


async def _setup_conn(conn: asyncpg.Connection) -> None:
    await register_vector(conn)


async def init_pool() -> asyncpg.Pool:
    global _pool
    if _pool is not None:
        return _pool
    if not config.PG_URI:
        raise RuntimeError("PG_URI not set")
    _pool = await asyncpg.create_pool(
        dsn=config.PG_URI,
        min_size=1,
        max_size=10,
        ssl=_ssl_context(),
        init=_setup_conn,
    )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("PG pool not initialized")
    return _pool


@asynccontextmanager
async def tenant_conn(tenant_id: str):
    """Acquire connection inside a transaction with app.tenant_id set for RLS.

    Switches role to RLS_ROLE so RLS enforces (superusers bypass RLS).
    Role + GUC scoped to the transaction via SET LOCAL.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(f"SET LOCAL ROLE {config.RLS_ROLE}")
            await conn.execute("SELECT set_config('app.tenant_id', $1, true)", str(tenant_id))
            yield conn


@asynccontextmanager
async def sys_conn():
    """Connection without tenant context. Used for tenant resolution / admin ops only."""
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn
