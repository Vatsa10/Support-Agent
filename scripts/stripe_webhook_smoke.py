"""Send a signed Stripe-shaped webhook to /webhooks/<tenant_id>/stripe.

Usage:
    python scripts/stripe_webhook_smoke.py <tenant_id> <webhook_secret> [base_url]

If [base_url] omitted, defaults to http://localhost:8000.
"""
import hashlib
import hmac
import json
import sys
import time

import httpx


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    tenant_id = sys.argv[1]
    secret = sys.argv[2]
    base = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8000"

    payload = {
        "id": "evt_smoke_" + str(int(time.time())),
        "type": "charge.refunded",
        "data": {"object": {"id": "re_smoke_001", "amount_refunded": 4820, "currency": "usd", "status": "succeeded"}},
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + raw, hashlib.sha256).hexdigest()
    header = f"t={ts},v1={sig}"

    r = httpx.post(
        f"{base}/webhooks/{tenant_id}/stripe",
        content=raw,
        headers={"Content-Type": "application/json", "Stripe-Signature": header},
        timeout=10.0,
    )
    print(f"{r.status_code} {r.text}")


if __name__ == "__main__":
    main()
