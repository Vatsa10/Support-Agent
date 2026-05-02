from typing import Optional
import redis.asyncio as redis

from config import config

_client: Optional[redis.Redis] = None


async def init_cache() -> redis.Redis:
    global _client
    if _client is not None:
        return _client
    if not config.VALKEY_URI:
        raise RuntimeError("VALKEY_URI not set")
    _client = redis.from_url(config.VALKEY_URI, decode_responses=True)
    await _client.ping()
    return _client


async def close_cache() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


def get_client() -> redis.Redis:
    if _client is None:
        raise RuntimeError("Valkey client not initialized")
    return _client


def tenant_key(tenant_id: str, *parts: str) -> str:
    return ":".join(["t", str(tenant_id), *parts])


async def incr_with_ttl(key: str, ttl_seconds: int) -> int:
    """Atomic INCR + EXPIRE on first increment. Returns new value."""
    client = get_client()
    pipe = client.pipeline()
    pipe.incr(key)
    pipe.expire(key, ttl_seconds, nx=True)
    res = await pipe.execute()
    return int(res[0])


async def setnx_idempotency(key: str, ttl_seconds: int) -> bool:
    """True if key reserved (first writer wins). False if already present."""
    client = get_client()
    return bool(await client.set(key, "1", nx=True, ex=ttl_seconds))


async def cache_get(key: str) -> Optional[str]:
    return await get_client().get(key)


async def cache_set(key: str, value: str, ttl_seconds: int) -> None:
    await get_client().set(key, value, ex=ttl_seconds)


async def cache_delete(key: str) -> None:
    await get_client().delete(key)
