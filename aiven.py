"""Smoke test: verify Aiven Postgres + Valkey reachable.

Reads PG_URI / PG_SSLROOTCERT / VALKEY_URI from .env. Run: python aiven.py
"""
import asyncio
import os
import sys
import ssl
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

load_dotenv()


async def check_pg() -> None:
    import asyncpg

    uri = os.getenv("PG_URI")
    if not uri:
        print("PG_URI not set; skipping")
        return

    ca = os.getenv("PG_SSLROOTCERT")
    ssl_ctx = None
    if ca:
        ssl_ctx = ssl.create_default_context(cafile=ca)
        ssl_ctx.check_hostname = True
        ssl_ctx.verify_mode = ssl.CERT_REQUIRED

    conn = await asyncpg.connect(dsn=uri, ssl=ssl_ctx)
    try:
        version = await conn.fetchval("SELECT version()")
        has_vec = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')"
        )
        print(f"PG OK: {version}")
        print(f"pgvector installed: {has_vec}")
    finally:
        await conn.close()


async def check_valkey() -> None:
    import redis.asyncio as redis

    uri = os.getenv("VALKEY_URI")
    if not uri:
        print("VALKEY_URI not set; skipping")
        return

    client = redis.from_url(uri, decode_responses=True)
    try:
        pong = await client.ping()
        print(f"Valkey OK: PING={pong}")
    finally:
        await client.close()


async def main() -> None:
    await check_pg()
    await check_valkey()


if __name__ == "__main__":
    asyncio.run(main())
