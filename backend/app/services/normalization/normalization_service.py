"""NormalizationService

Turns the raw, messy dict produced by URLExtractionService (+ optional
Gemini fallback fields) into the common `NormalizedProduct` structure,
so listings from completely different websites can be compared fairly.
"""

from __future__ import annotations

from typing import Any, Dict

from app.schemas.product import NormalizedProduct
from app.utils.text_utils import clean_whitespace, parse_currency, parse_price, parse_rating

WARRANTY_UNKNOWN = None
CONDITION_UNKNOWN = "unknown"


class NormalizationService:
    def normalize(self, raw: Dict[str, Any]) -> NormalizedProduct:
        price = raw.get("price")
        if not isinstance(price, (int, float)):
            price = parse_price(price)

        delivery_charge = raw.get("delivery_charge")
        if not isinstance(delivery_charge, (int, float)):
            delivery_charge = self._normalize_delivery_charge(raw.get("delivery_charge"), raw.get("description"))

        seller_rating = raw.get("seller_rating")
        if not isinstance(seller_rating, (int, float)):
            seller_rating = parse_rating(seller_rating)

        currency = raw.get("currency")
        if not currency:
            currency = parse_currency(raw.get("currency"), raw.get("price"))

        condition = self._normalize_condition(raw.get("condition"))
        warranty = self._normalize_warranty(raw.get("warranty"))

        specifications = raw.get("specifications")
        if not isinstance(specifications, dict):
            specifications = {}

        return NormalizedProduct(
            source_url=raw.get("source_url", ""),
            product_name=clean_whitespace(raw.get("product_name")),
            brand=clean_whitespace(raw.get("brand")),
            model=clean_whitespace(raw.get("model")),
            price=price,
            currency=currency,
            delivery_charge=delivery_charge,
            seller_name=clean_whitespace(raw.get("seller_name")),
            seller_rating=seller_rating,
            customer_rating=parse_rating(raw.get("customer_rating")) if not isinstance(raw.get("customer_rating"), float) else raw.get("customer_rating"),
            customer_rating_count=self._normalize_count(raw.get("customer_rating_count")),
            warranty=warranty,
            condition=condition,
            availability=clean_whitespace(raw.get("availability")),
            description=clean_whitespace(raw.get("description")),
            image=clean_whitespace(raw.get("image")),
            specifications=specifications,
            raw_source=raw.get("raw_source"),
            extraction_notes=raw.get("extraction_notes", []) or [],
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_delivery_charge(value: Any, description: Any) -> Any:
        parsed = parse_price(value)
        if parsed is not None:
            return parsed
        text = f"{value or ''} {description or ''}".lower()
        if "free delivery" in text or "free shipping" in text:
            return 0.0
        return None

    @staticmethod
    def _normalize_condition(value: Any) -> str:
        if not value:
            return CONDITION_UNKNOWN
        text = str(value).lower()
        if "refurb" in text:
            return "refurbished"
        if "used" in text or "pre-owned" in text or "preowned" in text:
            return "used"
        if "new" in text:
            return "new"
        return CONDITION_UNKNOWN

    @staticmethod
    def _normalize_count(value: Any) -> Any:
        if value is None:
            return None
        try:
            return int(float(str(value).replace(",", "")))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _normalize_warranty(value: Any) -> Any:
        if not value:
            return WARRANTY_UNKNOWN
        text = clean_whitespace(value)
        return text
