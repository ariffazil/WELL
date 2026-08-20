"""
well_triad.sanitize — F4 PII scanner + free-form input sanitizer.

Forged 2026-08-20.
Floors enforced: F4 (privacy).

Scans for: MY IC (12-digit), US SSN, credit card, email, MY phone,
street address. Returns the matching pattern label or None.
"""

from __future__ import annotations

import re
from typing import Optional

# PII pattern registry (extensible). Order matters — first match wins.
PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("MY_IC", re.compile(r"\b\d{12}\b")),
    ("US_SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("CREDIT_CARD", re.compile(r"\b\d{16}\b")),
    ("EMAIL", re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")),
    ("PHONE_MY", re.compile(r"\b0\d{9,10}\b")),
    ("STREET_ADDRESS", re.compile(r"\b\d{1,5}\s+\w+\s+(Street|St|Road|Rd|Avenue|Ave)\b")),
]


def scan_pii(value: Optional[str]) -> Optional[str]:
    """Return the matching PII pattern label if any, else None."""
    if not value:
        return None
    for label, pat in PII_PATTERNS:
        if pat.search(value):
            return label
    return None


def sanitize_note(note: Optional[str], max_len: int = 500) -> Optional[str]:
    """Trim and bound free-form note input."""
    if note is None:
        return None
    s = str(note).strip()
    return s[:max_len] if s else None