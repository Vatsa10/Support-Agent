"""Stripe Checkout for SaaS self-billing (tenants subscribing to Resolve).

Three routes:
  POST /billing/checkout-session  — tenant clicks "Upgrade" → returns Stripe URL
  POST /billing/portal            — open customer portal for self-service mgmt
  POST /billing/webhook           — Stripe → us, reconciles subscription status

Requires:
  STRIPE_API_KEY        sk_live_… (or sk_test_…)
  STRIPE_WEBHOOK_SECRET whsec_…
  STRIPE_PRICE_SCALE    price_…
  APP_URL               https://app.resolve.app  (used in return URLs)
"""
import hmac
import hashlib
import json
import os
import time
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from api.auth import Tenant, require_tenant
from db.pool import sys_conn, tenant_conn
from observability.logging import get_logger

router = APIRouter()
log = get_logger("billing")

STRIPE_API = "https://api.stripe.com/v1"


def _auth_headers() -> dict:
    key = os.getenv("STRIPE_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/x-www-form-urlencoded"}


def _app_url() -> str:
    return os.getenv("APP_URL", "http://localhost:3000")


def _price_for(plan: str) -> str:
    if plan == "scale":
        p = os.getenv("STRIPE_PRICE_SCALE")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {plan}")
    if not p:
        raise HTTPException(status_code=503, detail=f"Stripe price for {plan} not configured")
    return p


async def _stripe_form_post(path: str, form: list[tuple[str, str]]) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{STRIPE_API}{path}", data=form, headers=_auth_headers())
    if not r.is_success:
        raise HTTPException(status_code=r.status_code, detail=r.text[:240])
    return r.json()


class CheckoutBody(BaseModel):
    plan: str = "scale"
    email: Optional[str] = None


@router.post("/checkout-session")
async def create_checkout(body: CheckoutBody, tenant: Tenant = Depends(require_tenant)):
    price = _price_for(body.plan)
    app_url = _app_url()
    form = [
        ("mode", "subscription"),
        ("line_items[0][price]", price),
        ("line_items[0][quantity]", "1"),
        ("success_url", f"{app_url}/billing?session_id={{CHECKOUT_SESSION_ID}}"),
        ("cancel_url", f"{app_url}/billing?canceled=1"),
        ("client_reference_id", tenant.id),
        ("metadata[tenant_id]", tenant.id),
        ("subscription_data[metadata][tenant_id]", tenant.id),
    ]
    if body.email:
        form.append(("customer_email", body.email))
    data = await _stripe_form_post("/checkout/sessions", form)
    return {"url": data.get("url"), "id": data.get("id")}


@router.post("/portal")
async def create_portal(tenant: Tenant = Depends(require_tenant)):
    async with tenant_conn(tenant.id) as conn:
        row = await conn.fetchrow(
            "SELECT stripe_customer_id FROM billing_subscriptions WHERE tenant_id = current_setting('app.tenant_id')::uuid"
        )
    if not row or not row["stripe_customer_id"]:
        raise HTTPException(status_code=400, detail="No Stripe customer yet — start a subscription first")
    data = await _stripe_form_post(
        "/billing_portal/sessions",
        [("customer", row["stripe_customer_id"]), ("return_url", f"{_app_url()}/billing")],
    )
    return {"url": data.get("url")}


def _verify_stripe_sig(payload: bytes, sig_header: str, secret: str, tolerance: int = 300) -> bool:
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


@router.post("/webhook")
async def stripe_webhook(request: Request):
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="Stripe webhook secret not configured")
    sig = request.headers.get("stripe-signature")
    raw = await request.body()
    if not _verify_stripe_sig(raw, sig or "", secret):
        raise HTTPException(status_code=401, detail="Bad signature")
    event = json.loads(raw.decode("utf-8") or "{}")
    obj = (event.get("data") or {}).get("object") or {}
    ev_type = event.get("type", "")

    tenant_id = (obj.get("metadata") or {}).get("tenant_id") or obj.get("client_reference_id")
    if not tenant_id:
        # Look up by customer id if metadata missing
        cust = obj.get("customer")
        if cust:
            async with sys_conn() as conn:
                row = await conn.fetchrow(
                    "SELECT tenant_id FROM billing_subscriptions WHERE stripe_customer_id = $1",
                    cust,
                )
            if row:
                tenant_id = str(row["tenant_id"])

    if not tenant_id:
        log.warning("stripe_webhook_no_tenant", extra={"type": ev_type})
        return {"received": True}

    if ev_type == "checkout.session.completed":
        await _upsert_subscription(
            tenant_id,
            stripe_customer_id=obj.get("customer"),
            stripe_subscription_id=obj.get("subscription"),
            status="active",
        )
        await _set_plan(tenant_id, "scale")
    elif ev_type.startswith("customer.subscription."):
        await _upsert_subscription(
            tenant_id,
            stripe_customer_id=obj.get("customer"),
            stripe_subscription_id=obj.get("id"),
            status=obj.get("status", "unknown"),
        )
        if obj.get("status") in ("canceled", "incomplete_expired"):
            await _set_plan(tenant_id, "free")

    return {"received": True}


async def _upsert_subscription(
    tenant_id: str,
    *,
    stripe_customer_id: Optional[str],
    stripe_subscription_id: Optional[str],
    status: str,
) -> None:
    async with tenant_conn(tenant_id) as conn:
        await conn.execute(
            """
            INSERT INTO billing_subscriptions (tenant_id, stripe_customer_id, stripe_subscription_id, status)
            VALUES (current_setting('app.tenant_id')::uuid, $1, $2, $3)
            ON CONFLICT (tenant_id) DO UPDATE
              SET stripe_customer_id = COALESCE(EXCLUDED.stripe_customer_id, billing_subscriptions.stripe_customer_id),
                  stripe_subscription_id = COALESCE(EXCLUDED.stripe_subscription_id, billing_subscriptions.stripe_subscription_id),
                  status = EXCLUDED.status,
                  updated_at = now()
            """,
            stripe_customer_id, stripe_subscription_id, status,
        )


async def _set_plan(tenant_id: str, plan: str) -> None:
    async with sys_conn() as conn:
        await conn.execute("UPDATE tenants SET plan = $1 WHERE id = $2", plan, tenant_id)
