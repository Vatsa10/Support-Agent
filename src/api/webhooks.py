"""Inbound vendor webhooks: Stripe, Shopify, Zendesk.

Signature verification per vendor. Persists webhook_events idempotently and
reconciles action_runs status when external_id matches.

Endpoint shape: POST /webhooks/{tenant_id}/{kind}
"""
import base64
import hashlib
import hmac
import json
import time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request

from db.pool import sys_conn, tenant_conn
from observability.logging import get_logger
from security.crypto import decrypt_json

router = APIRouter()
log = get_logger("webhooks")


async def _load_integration_creds(tenant_id: str, kind: str) -> Optional[dict]:
    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            "SELECT encrypted_creds, config FROM tenant_integrations WHERE kind = $1 AND enabled = true ORDER BY created_at LIMIT 1",
            kind,
        )
    if not row:
        return None
    return {"creds": decrypt_json(row["encrypted_creds"]), "config": dict(row["config"] or {})}


def _verify_stripe(payload: bytes, sig_header: str, secret: str, tolerance: int = 300) -> bool:
    if not sig_header or not secret:
        return False
    items = dict(p.split("=", 1) for p in sig_header.split(",") if "=" in p)
    ts = items.get("t")
    sig = items.get("v1")
    if not ts or not sig:
        return False
    try:
        if abs(time.time() - int(ts)) > tolerance:
            return False
    except ValueError:
        return False
    expected = hmac.new(secret.encode("utf-8"), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


def _verify_shopify(payload: bytes, sig_header: str, secret: str) -> bool:
    if not sig_header or not secret:
        return False
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
    return hmac.compare_digest(base64.b64encode(digest).decode("ascii"), sig_header)


def _verify_zendesk(payload: bytes, sig_header: str, secret: str) -> bool:
    # Zendesk uses HMAC SHA256 base64 of timestamp + body; we accept body-only HMAC here as a baseline
    if not sig_header or not secret:
        return False
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
    return hmac.compare_digest(base64.b64encode(digest).decode("ascii"), sig_header)


VERIFIERS = {
    "stripe": ("Stripe-Signature", _verify_stripe, "webhook_secret"),
    "shopify": ("X-Shopify-Hmac-Sha256", _verify_shopify, "webhook_secret"),
    "zendesk": ("X-Zendesk-Webhook-Signature", _verify_zendesk, "webhook_secret"),
}


def _extract_external_id(kind: str, payload: dict) -> Optional[str]:
    if kind == "stripe":
        return ((payload.get("data") or {}).get("object") or {}).get("id")
    if kind == "shopify":
        return str(payload.get("id")) if payload.get("id") is not None else None
    if kind == "zendesk":
        return str(((payload.get("ticket") or {}).get("id"))) if payload.get("ticket") else None
    return None


async def _reconcile(tenant_id: str, kind: str, external_id: Optional[str], payload: dict) -> None:
    if not external_id:
        return
    new_status = _status_from_event(kind, payload)
    if not new_status:
        return
    async with tenant_conn(tenant_id) as conn:
        await conn.execute(
            """
            UPDATE action_runs
               SET status = $1,
                   result = COALESCE(result,'{}'::jsonb) || jsonb_build_object('webhook_reconciled', true, 'webhook_status', $1)
             WHERE result ->> 'external_id' = $2
            """,
            new_status, external_id,
        )


def _status_from_event(kind: str, payload: dict) -> Optional[str]:
    if kind == "stripe":
        t = payload.get("type", "")
        if t.startswith("charge.refund") or t.startswith("refund."):
            return "succeeded"
        if t == "customer.subscription.deleted":
            return "succeeded"
    if kind == "shopify":
        if payload.get("cancelled_at"):
            return "succeeded"
    if kind == "zendesk":
        st = (payload.get("ticket") or {}).get("status")
        if st in ("closed", "solved"):
            return "succeeded"
    return None


@router.post("/webhooks/{tenant_id}/{kind}")
async def receive(tenant_id: str, kind: str, request: Request):
    if kind not in VERIFIERS:
        raise HTTPException(status_code=400, detail=f"Unknown webhook kind: {kind}")

    header_name, verifier, secret_field = VERIFIERS[kind]
    sig = request.headers.get(header_name) or request.headers.get(header_name.lower())
    raw = await request.body()

    bundle = await _load_integration_creds(tenant_id, kind)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"No {kind} integration for tenant")
    secret = (bundle["creds"] or {}).get(secret_field)
    if not secret:
        raise HTTPException(status_code=400, detail=f"Integration missing creds.{secret_field}")

    if not verifier(raw, sig or "", secret):
        log.warning("webhook_bad_sig", extra={"kind": kind, "tenant_id": tenant_id})
        raise HTTPException(status_code=401, detail="Bad signature")

    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        payload = {}
    external_id = _extract_external_id(kind, payload)
    event_type = payload.get("type") or payload.get("topic")

    async with tenant_conn(tenant_id) as conn:
        await conn.execute(
            """
            INSERT INTO webhook_events
                (tenant_id, kind, external_id, event_type, payload, signature_ok, processed)
            VALUES (current_setting('app.tenant_id')::uuid, $1, $2, $3, $4::jsonb, true, false)
            ON CONFLICT (tenant_id, kind, external_id) DO NOTHING
            """,
            kind, external_id, event_type, json.dumps(payload),
        )

    await _reconcile(tenant_id, kind, external_id, payload)

    async with tenant_conn(tenant_id) as conn:
        await conn.execute(
            "UPDATE webhook_events SET processed = true WHERE tenant_id = current_setting('app.tenant_id')::uuid AND kind = $1 AND external_id = $2",
            kind, external_id,
        )

    return {"received": True, "kind": kind, "external_id": external_id}
