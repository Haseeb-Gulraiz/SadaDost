"""Deterministic safety floor — the hard guarantee that does NOT depend on any LLM.

OpenAI Guardrails (see llm.py) is the configurable layer. This module is the floor:
even if the model or the service misbehaves, a reply can never carry restricted PII.

Two checks:
  1. Exact-match redaction of the loaded customer's own restricted values.
  2. Regex redaction of PK-format CNIC / IBAN / full card numbers in general.
"""
import re

REDACTION = "[REDACTED]"

# Pakistani CNIC: 5 digits - 7 digits - 1 digit  (e.g. 42101-1234567-8)
_CNIC = re.compile(r"\b\d{5}-\d{7}-\d\b")
# IBAN (Pakistan): PK + 2 check digits + 4 bank letters + 16 digits, spaces tolerated.
_IBAN = re.compile(r"\bPK\d{2}[A-Z0-9]{4}\d{6,}\b", re.IGNORECASE)
# A full 16-digit card number (grouped or not). Masked PANs (with *) are left alone.
_CARD = re.compile(r"\b(?:\d[ -]?){13,16}\d\b")

_PATTERNS = (_CNIC, _IBAN, _CARD)


def scrub(text: str, restricted_values: list[str] | None = None) -> tuple[str, bool]:
    """Redact restricted PII from `text`.

    Returns (clean_text, found) where `found` is True if anything was redacted.
    """
    found = False
    cleaned = text

    # 1) Exact values for THIS customer (strongest, no false positives).
    for value in restricted_values or []:
        if value and value in cleaned:
            cleaned = cleaned.replace(value, REDACTION)
            found = True

    # 2) Generic PK-format patterns (defense in depth for anything we didn't enumerate).
    for pattern in _PATTERNS:
        if pattern.search(cleaned):
            cleaned = pattern.sub(REDACTION, cleaned)
            found = True

    return cleaned, found
