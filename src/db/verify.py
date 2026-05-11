"""Read-only verification: extensions, tables, RLS policies, app_user role."""
import asyncio
import os
import ssl
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from db._dns_patch import install as _install_dns_fallback
_install_dns_fallback()

import asyncpg
from dotenv import load_dotenv

load_dotenv()


def _ssl_ctx():
    ca = os.getenv("PG_SSLROOTCERT")
    if not ca:
        return None
    ctx = ssl.create_default_context(cafile=ca)
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


async def main():
    conn = await asyncpg.connect(dsn=os.environ["PG_URI"], ssl=_ssl_ctx())
    try:
        exts = await conn.fetch("SELECT extname FROM pg_extension ORDER BY extname")
        print("Extensions:", [r["extname"] for r in exts])
        roles = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='app_user')")
        print("app_user role:", roles)
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        )
        print("Tables:")
        for r in tables:
            print(f"  - {r['tablename']}")
        pols = await conn.fetch(
            "SELECT tablename, policyname AS polname FROM pg_policies WHERE schemaname='public' ORDER BY tablename"
        )
        print(f"RLS policies ({len(pols)}):")
        for r in pols:
            print(f"  - {r['tablename']:25} {r['polname']}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
