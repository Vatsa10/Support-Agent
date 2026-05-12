"""Multi-provider LLM abstraction with per-tenant override.

Providers: google (Gemini), anthropic (Claude), openai (GPT). All return a
uniform `LLMResult` so the ReACT loop and tools don't care which model ran.

Per-tenant config lives in `llm_configs` (provider/model/temperature + encrypted
API key). Fallback to env defaults (`LLM_PROVIDER`, `LLM_MODEL`, `LLM_TEMPERATURE`).
"""
import json
import os
from dataclasses import dataclass
from typing import Optional

import httpx

from config import config
from db.pool import tenant_conn
from security.crypto import decrypt_json


@dataclass
class LLMResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    provider: str = ""


# ============================================================
# Providers
# ============================================================

async def _gemini(model: str, prompt: str, temperature: float, api_key: str) -> LLMResult:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": 1024},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, json=body)
    r.raise_for_status()
    d = r.json()
    text = (((d.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [{}])[0].get("text", "")
    um = d.get("usageMetadata") or {}
    return LLMResult(
        text=text,
        input_tokens=int(um.get("promptTokenCount", 0) or 0),
        output_tokens=int(um.get("candidatesTokenCount", 0) or 0),
        model=model,
        provider="google",
    )


async def _anthropic(model: str, prompt: str, temperature: float, api_key: str) -> LLMResult:
    body = {
        "model": model,
        "max_tokens": 1024,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            json=body,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
    r.raise_for_status()
    d = r.json()
    text = "".join(b.get("text", "") for b in (d.get("content") or []) if b.get("type") == "text")
    u = d.get("usage") or {}
    return LLMResult(
        text=text,
        input_tokens=int(u.get("input_tokens", 0)),
        output_tokens=int(u.get("output_tokens", 0)),
        model=model,
        provider="anthropic",
    )


async def _openai(model: str, prompt: str, temperature: float, api_key: str) -> LLMResult:
    body = {
        "model": model,
        "temperature": temperature,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
    r.raise_for_status()
    d = r.json()
    text = (((d.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
    u = d.get("usage") or {}
    return LLMResult(
        text=text,
        input_tokens=int(u.get("prompt_tokens", 0)),
        output_tokens=int(u.get("completion_tokens", 0)),
        model=model,
        provider="openai",
    )


PROVIDERS = {"google": _gemini, "anthropic": _anthropic, "openai": _openai}


# ============================================================
# Tenant resolution
# ============================================================

async def get_provider_for(tenant_id: Optional[str]) -> tuple[str, str, float, str]:
    """Returns (provider, model, temperature, api_key) for a tenant.

    Order: tenant `llm_configs` row → env var fallback (Gemini default).
    """
    provider = os.getenv("LLM_PROVIDER", "google")
    model = os.getenv("LLM_MODEL", config.LLM_MODEL)
    temperature = float(os.getenv("LLM_TEMPERATURE", config.LLM_TEMPERATURE))
    api_key = os.getenv("GOOGLE_API_KEY", "") if provider == "google" else os.getenv("LLM_API_KEY", "")

    if tenant_id:
        try:
            async with tenant_conn(tenant_id) as conn:
                row = await conn.fetchrow(
                    "SELECT provider, model, temperature, encrypted_creds FROM llm_configs WHERE tenant_id = current_setting('app.tenant_id')::uuid"
                )
            if row:
                provider = row["provider"]
                model = row["model"]
                temperature = float(row["temperature"])
                if row["encrypted_creds"]:
                    creds = decrypt_json(bytes(row["encrypted_creds"]))
                    api_key = creds.get("api_key", "") or api_key
        except Exception:
            pass

    return provider, model, temperature, api_key


async def generate(prompt: str, tenant_id: Optional[str] = None) -> LLMResult:
    provider, model, temperature, api_key = await get_provider_for(tenant_id)
    fn = PROVIDERS.get(provider)
    if not fn:
        raise RuntimeError(f"Unknown LLM provider: {provider}")
    if not api_key:
        raise RuntimeError(f"Missing API key for provider {provider}")
    return await fn(model, prompt, temperature, api_key)
