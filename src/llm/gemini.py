"""Thin wrapper over the new `google.genai` SDK.

Replaces the deprecated `google.generativeai` package. One module-level Client
is created lazily on first use; reused thereafter.
"""
from functools import lru_cache
from typing import Optional

from google import genai
from google.genai import types

from config import config


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    return genai.Client(api_key=config.GOOGLE_API_KEY)


def generate_text(
    prompt: str,
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    system_instruction: Optional[str] = None,
    contents: Optional[list] = None,
):
    """Returns the raw response object so callers can read .text and .usage_metadata."""
    cfg_kwargs: dict = {}
    if temperature is not None:
        cfg_kwargs["temperature"] = temperature
    if max_output_tokens is not None:
        cfg_kwargs["max_output_tokens"] = max_output_tokens
    if system_instruction is not None:
        cfg_kwargs["system_instruction"] = system_instruction
    cfg = types.GenerateContentConfig(**cfg_kwargs) if cfg_kwargs else None

    return _client().models.generate_content(
        model=model or config.LLM_MODEL,
        contents=contents if contents is not None else prompt,
        config=cfg,
    )


def embed(text: str, *, task_type: str = "RETRIEVAL_DOCUMENT", model: Optional[str] = None) -> list[float]:
    """Returns the dense embedding vector for `text`.

    Forces output dimensionality to config.EMBEDDING_DIM so vectors match the
    pgvector index width.
    """
    resp = _client().models.embed_content(
        model=model or config.DENSE_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=config.EMBEDDING_DIM,
        ),
    )
    embs = resp.embeddings
    if not embs:
        return []
    return list(getattr(embs[0], "values", []) or [])


def usage_pair(response) -> tuple[int, int]:
    """Extract (prompt_tokens, output_tokens) from a generate_content response."""
    um = getattr(response, "usage_metadata", None)
    if not um:
        return 0, 0
    in_tok = int(getattr(um, "prompt_token_count", 0) or 0)
    out_tok = int(getattr(um, "candidates_token_count", 0) or 0)
    return in_tok, out_tok
