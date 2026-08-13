"""Small, defensive helper functions used by the extraction/normalization
services. Centralized here so we never repeat unsafe `.strip()` /
`.replace()` calls on values that might actually be lists (BeautifulSoup
returns AttributeValueList for some multi-valued attributes, e.g.
`content` on some meta tags, or `class`).
"""

from __future__ import annotations

import re
from typing import Any, Optional


def safe_str(value: Any) -> Optional[str]:
    """Coerce a BeautifulSoup attribute value (str, list, None, etc.) into a
    clean string, or None if there is nothing usable."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        # BeautifulSoup AttributeValueList - join if it's a list of strings
        parts = [str(v).strip() for v in value if v is not None and str(v).strip()]
        if not parts:
            return None
        return " ".join(parts)
    text = str(value).strip()
    return text or None


def clean_whitespace(value: Any) -> Optional[str]:
    text = safe_str(value)
    if text is None:
        return None
    return re.sub(r"\s+", " ", text).strip() or None


_PRICE_RE = re.compile(r"[-+]?\d[\d,]*\.?\d*")

_CURRENCY_SYMBOLS = {
    "₹": "INR",
    "rs.": "INR",
    "rs": "INR",
    "inr": "INR",
    "$": "USD",
    "usd": "USD",
    "€": "EUR",
    "eur": "EUR",
    "£": "GBP",
    "gbp": "GBP",
}


def parse_price(value: Any) -> Optional[float]:
    """Extract a numeric price from strings like '₹47,999', 'Rs. 47,999',
    'INR 47999', 47999.0, etc. Returns None (never 0) when unknown."""
    text = safe_str(value)
    if text is None:
        return None
    match = _PRICE_RE.search(text.replace(",", ""))
    if not match:
        return None
    try:
        return round(float(match.group()), 2)
    except (ValueError, TypeError):
        return None


def parse_currency(value: Any, fallback_text: Any = None) -> Optional[str]:
    """Detect a normalized ISO-ish currency code from a currency field or
    from surrounding price text (e.g. '₹47,999' -> INR)."""
    for candidate in (value, fallback_text):
        text = safe_str(candidate)
        if not text:
            continue
        lowered = text.lower()
        for symbol, code in _CURRENCY_SYMBOLS.items():
            if symbol in lowered:
                return code
        # Already looks like an ISO code, e.g. "INR", "USD"
        if re.fullmatch(r"[A-Za-z]{3}", text.strip()):
            return text.strip().upper()
    return None


def parse_rating(value: Any) -> Optional[float]:
    """Normalize a seller/product rating onto a 0-5 scale."""
    text = safe_str(value)
    if text is None:
        return None
    match = re.search(r"\d+(\.\d+)?", text)
    if not match:
        return None
    try:
        rating = float(match.group())
    except ValueError:
        return None
    if rating > 5:
        # Handle ratings given out of 10 or 100
        if rating <= 10:
            rating = rating / 2
        elif rating <= 100:
            rating = rating / 20
    return round(max(0.0, min(rating, 5.0)), 2)


def strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` style code fences that LLMs often wrap
    JSON responses in."""
    if not text:
        return text
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()
