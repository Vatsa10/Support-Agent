import asyncio
from pathlib import Path

from db.pool import init_pool, close_pool, sys_conn

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


async def apply_schema() -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    await init_pool()
    try:
        async with sys_conn() as conn:
            await conn.execute(sql)
        print(f"Schema applied from {SCHEMA_PATH}")
    finally:
        await close_pool()


def main() -> None:
    asyncio.run(apply_schema())


if __name__ == "__main__":
    main()
