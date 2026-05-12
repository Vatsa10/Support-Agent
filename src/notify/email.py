"""Email delivery via Resend (https://resend.com). HTTP API, no SDK dependency.

If RESEND_API_KEY is unset, logs the message instead of sending (dev-friendly).
"""
import os
from typing import Optional

import httpx

from observability.logging import get_logger

log = get_logger("notify.email")

RESEND_API = "https://api.resend.com/emails"


class EmailDisabled(RuntimeError):
    pass


def _api_key() -> Optional[str]:
    k = os.getenv("RESEND_API_KEY")
    return k or None


def _from_addr() -> str:
    return os.getenv("EMAIL_FROM", "Resolve <notifications@resolve.app>")


async def send_email(
    to: str,
    subject: str,
    html: str,
    *,
    text: Optional[str] = None,
    tag: Optional[str] = None,
) -> dict:
    key = _api_key()
    if not key:
        log.info(
            "email_logged_only",
            extra={"to": to, "subject": subject, "tag": tag, "len": len(html)},
        )
        return {"ok": True, "logged_only": True}

    body = {
        "from": _from_addr(),
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        body["text"] = text
    if tag:
        body["tags"] = [{"name": "type", "value": tag}]

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            RESEND_API,
            json=body,
            headers={"Authorization": f"Bearer {key}"},
        )
    ok = resp.is_success
    if not ok:
        log.warning("email_send_failed", extra={"status": resp.status_code, "body": resp.text[:240]})
    return {"ok": ok, "status_code": resp.status_code, "data": resp.json() if ok else None}
