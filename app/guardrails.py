"""Task 10: input-side guardrails (PII masking, prompt-injection, validation)
and output-side groundedness helpers."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

MAX_QUERY_CHARS = 1000

# Fixed-format PII.  Order matters: Aadhaar (12 digits) is tried before generic accounts.
PII_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("PAN", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")),
    ("AADHAAR", re.compile(r"\b[2-9][0-9]{3}[ -]?[0-9]{4}[ -]?[0-9]{4}\b")),
    ("BANK_ACCOUNT", re.compile(r"\b[0-9]{9,18}\b")),
]

INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above|earlier) (instructions|prompts?|rules)",
    r"disregard (all |any |the )?(previous|prior|above|your) (instructions|prompts?|rules)",
    r"(reveal|show|print|repeat|leak) (me )?(your|the) (system|hidden|initial) (prompt|instructions)",
    r"you are now (?!a loan)",
    r"act as (?:an? )?(?:unrestricted|jailbroken|dan)\b",
    r"\bdeveloper mode\b",
    r"\bjailbreak\b",
    r"override (your|the) (safety|guardrails|rules|instructions)",
    r"pretend (you have|there are) no (rules|restrictions)",
]
_INJ = [re.compile(p, re.I) for p in INJECTION_PATTERNS]


@dataclass
class InputCheck:
    ok: bool
    masked_text: str
    pii_found: list[str] = field(default_factory=list)
    injection: bool = False
    reason: str | None = None


def mask_pii(text: str) -> tuple[str, list[str]]:
    found: list[str] = []
    for label, pat in PII_PATTERNS:
        def _sub(m, label=label):
            found.append(label)
            return f"[{label}_MASKED]"
        text = pat.sub(_sub, text)
    return text, found


def detect_injection(text: str) -> bool:
    return any(p.search(text) for p in _INJ)


def check_input(text: str) -> InputCheck:
    """Validate, mask PII and detect injection. Masking runs first so that
    nothing downstream (model, logs, memory) ever sees fixed-format PII."""
    if not isinstance(text, str) or not text.strip():
        return InputCheck(False, "", reason="empty_query")
    if len(text) > MAX_QUERY_CHARS:
        return InputCheck(False, "", reason="query_too_long")
    masked, found = mask_pii(text)
    inj = detect_injection(masked)
    return InputCheck(ok=not inj, masked_text=masked, pii_found=sorted(set(found)),
                      injection=inj, reason="prompt_injection" if inj else None)


# ---- output side ---------------------------------------------------------
_STOP = set("a an the of to in on for and or is are was be it its as at by with from that this "
            "what which how do does can i my me you your we our if than then so not no any".split())


def content_tokens(text: str) -> set[str]:
    toks = re.findall(r"[a-z0-9]+", text.lower())
    return {t.rstrip("s") if len(t) > 3 else t for t in toks if t not in _STOP}


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", text.strip())
    return [p.strip() for p in parts if p.strip()]


def support_ratio(answer: str, contexts: list[str]) -> float:
    """Fraction of answer sentences whose content tokens are >=70 % present in the
    retrieved context (lexical grounding signal used under MOCK_LLM)."""
    ctx: set[str] = set()
    for c in contexts:
        ctx |= content_tokens(c)
    sents = sentences(answer)
    if not sents:
        return 0.0
    ok = 0
    for s in sents:
        toks = content_tokens(s)
        if not toks or len(toks & ctx) / len(toks) >= 0.7:
            ok += 1
    return ok / len(sents)
