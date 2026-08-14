"""AI Product Comparator - FastAPI backend entrypoint.

Endpoints:
    GET  /                health check
    GET  /health           health status
    POST /extract-url      extract a single product listing
    POST /compare-urls     extract, normalize, match, score, rank and
                            recommend across 2+ product URLs

Run with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.schemas.product import (
    CompareUrlsRequest,
    CompareUrlsResponse,
    ExtractUrlRequest,
    NormalizedProduct,
)
from app.services.gemini.gemini_service import GeminiService
from app.services.matching.matching_service import MatchingService
from app.services.normalization.normalization_service import NormalizationService
from app.services.recommendation.recommendation_service import RecommendationService
from app.services.scoring.deal_scoring_service import DealScoringService
from app.services.url.url_extraction_service import URLExtractionService
from app.services.url.playwright_extraction_service import PlaywrightExtractionService
from app.utils.errors import AppError, InsufficientListingsError

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_product_comparator")

app = FastAPI(
    title="AI Product Comparator",
    description="Paste product links from different sellers and let AI compare "
    "prices, specifications, sellers, warranty, and overall deal quality.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services are stateless and cheap to construct; instantiate once.
url_service = URLExtractionService()
playwright_service = PlaywrightExtractionService()
gemini_service = GeminiService()
normalization_service = NormalizationService()
matching_service = MatchingService()
scoring_service = DealScoringService()
recommendation_service = RecommendationService()


# ----------------------------------------------------------------------
# Global error handling - never leak raw tracebacks to the frontend.
# ----------------------------------------------------------------------
@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    logger.warning("Handled error on %s: %s", request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong while processing your request. Please try again."},
    )


# ----------------------------------------------------------------------
# Health endpoints
# ----------------------------------------------------------------------
@app.get("/")
async def root():
    return {"status": "ok", "service": "AI Product Comparator"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# ----------------------------------------------------------------------
# Core extraction pipeline (shared by both endpoints)
# ----------------------------------------------------------------------
def _extract_and_normalize(url: str) -> NormalizedProduct:
    url = url_service.validate_url(url)
    try:
        raw = url_service.extract(url)
        missing_core = not raw.get("product_name") or raw.get("price") is None
    except Exception as exc:
        from urllib.parse import urlparse as _up
        _domain = _up(url).netloc.replace("www.", "").split(".")[0].title()
        raw = {
            "source_url": url,
            "seller_name": _domain,
            "extraction_notes": [f"Lightweight scraper blocked or failed (HTTP error/timeout). Trying browser fallback."]
        }
        missing_core = True

    if missing_core:
        pw_html = playwright_service.fetch_html(url)
        if pw_html:
            from bs4 import BeautifulSoup as _BS
            pw_soup = _BS(pw_html, "html.parser")
            pw_raw = {"source_url": url, "raw_source": pw_html[:60000]}

            # Carry over domain-based seller seed
            from urllib.parse import urlparse as _up
            _domain = _up(url).netloc.replace("www.", "").split(".")[0].title()
            pw_raw["seller_name"] = _domain

            # Run all extraction layers on the rendered HTML
            for extractor in [
                url_service._extract_json_ld,
                url_service._extract_opengraph,
                url_service._extract_meta_tags,
                url_service._extract_visible_html,
            ]:
                layer = extractor(pw_soup)
                for k, v in layer.items():
                    if not pw_raw.get(k) and v:
                        pw_raw[k] = v

            pw_raw["extraction_notes"] = raw.get("extraction_notes", []) + [
                "Playwright browser rendering was used for this page."
            ]
            # Use playwright result if it found more data
            if pw_raw.get("product_name") or pw_raw.get("price"):
                raw = pw_raw
                missing_core = not raw.get("product_name") or raw.get("price") is None

    # AI-assisted fallback only kicks in when structural extraction left
    # required fields empty, and only if a Gemini API key is configured.
    if missing_core and gemini_service.api_key:
        try:
            page_text = BeautifulSoup(raw.get("raw_source") or "", "html.parser").get_text(" ", strip=True)
            ai_fields = gemini_service.extract_missing_fields(page_text, raw, url)
            for key, value in ai_fields.items():
                if not raw.get(key):
                    raw[key] = value
            if ai_fields:
                raw.setdefault("extraction_notes", []).append(
                    "AI extraction was used to fill in missing details."
                )
        except AppError as exc:
            raw.setdefault("extraction_notes", []).append(exc.detail)

    return normalization_service.normalize(raw)


# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------
@app.post("/extract-url", response_model=NormalizedProduct)
async def extract_url(payload: ExtractUrlRequest):
    return _extract_and_normalize(payload.url)


@app.post("/compare-urls", response_model=CompareUrlsResponse)
async def compare_urls(payload: CompareUrlsRequest):
    urls = [u.strip() for u in payload.urls if u and u.strip()]
    if len(urls) < 2:
        raise InsufficientListingsError()

    listings = [_extract_and_normalize(url) for url in urls]

    comparisons = matching_service.compare_all(listings)
    matched_count = sum(1 for c in comparisons if c.is_match) + 1  # +1 for the reference listing

    ranked_deals = scoring_service.score_all(listings)
    recommendation = recommendation_service.recommend(listings, ranked_deals)

    return CompareUrlsResponse(
        listing_count=len(listings),
        listings=listings,
        comparisons=comparisons,
        matched_listing_count=matched_count,
        ranked_deals=ranked_deals,
        recommendation=recommendation,
    )
