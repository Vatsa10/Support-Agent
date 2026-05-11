"""Best-effort prompt-injection guard.

Strips obvious instruction overrides from retrieved KB context before injection.
Not a substitute for output validation + policy gating; defense in depth.
"""
import re

REDACTED = "[redacted by safety filter]"

PATTERNS = [
    re.compile(r"^\s*(ignore|disregard).{0,40}(previous|prior|above).{0,40}(instruction|prompt|rule)", re.I | re.M),
    re.compile(r"^\s*system\s*:\s", re.I | re.M),
    re.compile(r"^\s*assistant\s*:\s", re.I | re.M),
    re.compile(r"^\s*you\s+are\s+now\s+", re.I | re.M),
    re.compile(r"^\s*forget\s+(everything|all|previous)", re.I | re.M),
    re.compile(r"^\s*new\s+(instructions|task|role)\s*:\s", re.I | re.M),
    re.compile(r"<\|.*?\|>"),  # ChatML-ish sentinels
]


def is_prompt_injection(text: str) -> bool:
    return any(p.search(text or "") for p in PATTERNS)


def scrub_context(text: str) -> str:
    if not text:
        return text
    out = text
    for p in PATTERNS:
        out = p.sub(REDACTED, out)
    return out
