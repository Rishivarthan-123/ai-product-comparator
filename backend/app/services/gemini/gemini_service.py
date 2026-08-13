"""GeminiService

Wraps the Google Gemini Developer API (via the official `google-genai`
Python SDK) to fill in product fields that could not be found through
structured extraction (JSON-LD / OpenGraph / meta tags / visible HTML).

Design goals:
    * Never crash the request pipeline - any Gemini failure is converted
      into a handled AppError (AIServiceUnavailableError / AIQuotaExceededError)
      or simply results in `None` fields being kept as-is.
    * Never assume the model returns valid JSON - response text is
      cleaned of markdown fences and safely parsed with fallbacks.
    * Never use `additionalProperties` / enterprise-only response schema
      features - we ask for plain JSON via prompting + parsing instead of
      passing a strict `response_schema`, keeping this compatible with the
      standard Gemini Developer API.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from app.utils.errors import AIQuotaExceededError, AIServiceUnavailableError
from app.utils.text_utils import strip_markdown_fences

GEMINI_MODEL = "gemini-2.5-flash"

REQUIRED_FIELDS = [
    "product_name",
    "brand",
    "model",
    "price",
    "currency",
    "delivery_charge",
    "seller_name",
    "seller_rating",
    "customer_rating",
    "customer_rating_count",
    "warranty",
    "condition",
    "availability",
    "description",
]


class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client = None

    # ------------------------------------------------------------------
    def _get_client(self):
        if not self.api_key:
            raise AIServiceUnavailableError(
                "AI extraction is temporarily unavailable. Please try again."
            )
        if self._client is None:
            try:
                from google import genai  # Imported lazily so the app can
                # still start even if the package isn't installed yet.
            except ImportError as exc:
                raise AIServiceUnavailableError(
                    "AI extraction is temporarily unavailable. Please try again."
                ) from exc
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    # ------------------------------------------------------------------
    def extract_missing_fields(
        self, page_text: str, known_fields: Dict[str, Any], source_url: str
    ) -> Dict[str, Any]:
        """Ask Gemini to fill in only the fields we could not extract
        structurally. Returns a dict containing just the newly-found
        fields (never overwrites fields we already trust)."""

        missing = [f for f in REQUIRED_FIELDS if not known_fields.get(f)]
        if not missing:
            return {}

        client = self._get_client()
        prompt = self._build_prompt(page_text, known_fields, missing, source_url)

        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
        except Exception as exc:  # noqa: BLE001 - SDK raises various error types
            message = str(exc).lower()
            if "quota" in message or "rate limit" in message or "429" in message:
                raise AIQuotaExceededError() from exc
            raise AIServiceUnavailableError() from exc

        text = getattr(response, "text", None)
        if not text:
            # Empty response from the model - treat as unavailable rather
            # than crashing.
            return {}

        parsed = self._safe_parse_json(text)
        if not parsed:
            return {}

        # Only keep fields we actually asked for and that are still empty.
        cleaned: Dict[str, Any] = {}
        for field in missing:
            value = parsed.get(field)
            if value in (None, "", "null", "unknown", "N/A"):
                continue
            cleaned[field] = value
        return cleaned

    # ------------------------------------------------------------------
    @staticmethod
    def _build_prompt(
        page_text: str, known_fields: Dict[str, Any], missing: list[str], source_url: str
    ) -> str:
        truncated_text = (page_text or "")[:20000]
        return f"""You are extracting structured e-commerce product data from raw webpage
text. You must respond with ONLY a valid JSON object and nothing else -
no markdown code fences, no commentary, no explanation.

Source URL: {source_url}

Fields already known (do not change these): {json.dumps(known_fields, default=str)}

Fields to find, using ONLY information present in the page text below.
If a field truly cannot be determined from the text, use the JSON value
null - never invent or guess a value:
{json.dumps(missing)}

Return a single flat JSON object with exactly these keys: {json.dumps(missing)}

Page text:
\"\"\"
{truncated_text}
\"\"\"
"""

    @staticmethod
    def _safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
        cleaned = strip_markdown_fences(text)
        try:
            parsed = json.loads(cleaned)
            return parsed if isinstance(parsed, dict) else None
        except (json.JSONDecodeError, TypeError):
            pass

        # Last resort: try to locate the first {...} block in the text.
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = cleaned[start : end + 1]
            try:
                parsed = json.loads(snippet)
                return parsed if isinstance(parsed, dict) else None
            except (json.JSONDecodeError, TypeError):
                return None
        return None
