"""Shared HTTP helper for connectors: retry + circuit breaker.

Circuit breaker counter lives in Valkey keyed by (tenant_id, kind).
After CONNECTOR_BREAKER_THRESHOLD consecutive failures, calls short-circuit
for CONNECTOR_BREAKER_COOLDOWN_S seconds.
"""
import os
from typing import Optional

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from cache.valkey import get_client, tenant_key
from observability.logging import get_logger

log = get_logger("connector.http")

BREAKER_THRESHOLD = int(os.getenv("CONNECTOR_BREAKER_THRESHOLD", "5"))
BREAKER_COOLDOWN_S = int(os.getenv("CONNECTOR_BREAKER_COOLDOWN_S", "60"))


class IntegrationUnhealthy(RuntimeError):
    pass


def _breaker_key(tenant_id: str, kind: str) -> str:
    return tenant_key(tenant_id, "breaker", kind)


def _open_key(tenant_id: str, kind: str) -> str:
    return tenant_key(tenant_id, "breaker_open", kind)


async def _is_open(tenant_id: str, kind: str) -> bool:
    return bool(await get_client().get(_open_key(tenant_id, kind)))


async def _record_failure(tenant_id: str, kind: str) -> None:
    client = get_client()
    n = await client.incr(_breaker_key(tenant_id, kind))
    await client.expire(_breaker_key(tenant_id, kind), BREAKER_COOLDOWN_S)
    if n >= BREAKER_THRESHOLD:
        await client.set(_open_key(tenant_id, kind), "1", ex=BREAKER_COOLDOWN_S)
        log.warning("breaker_open", extra={"tenant_id": tenant_id, "kind": kind, "fails": n})


async def _record_success(tenant_id: str, kind: str) -> None:
    client = get_client()
    await client.delete(_breaker_key(tenant_id, kind))
    await client.delete(_open_key(tenant_id, kind))


async def request_with_retry(
    *,
    tenant_id: str,
    kind: str,
    method: str,
    url: str,
    headers: Optional[dict] = None,
    json: Optional[dict] = None,
    data: Optional[dict] = None,
    timeout: float = 20.0,
) -> httpx.Response:
    if await _is_open(tenant_id, kind):
        raise IntegrationUnhealthy(f"{kind} circuit open for tenant")

    retryable = (httpx.TransportError, httpx.ReadTimeout, httpx.ConnectError)

    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type(retryable),
        reraise=True,
    ):
        with attempt:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.request(
                    method, url, headers=headers, json=json, data=data
                )

    # 5xx counts as failure for the breaker; success otherwise
    if resp.status_code >= 500:
        await _record_failure(tenant_id, kind)
    else:
        await _record_success(tenant_id, kind)
    return resp
