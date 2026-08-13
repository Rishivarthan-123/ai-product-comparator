"""Pydantic schemas used across the AI Product Comparator backend."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class ExtractUrlRequest(BaseModel):
    url: str = Field(..., description="Product page URL to extract information from")


class CompareUrlsRequest(BaseModel):
    urls: List[str] = Field(..., min_length=2, description="List of product URLs to compare (min 2)")


class NormalizedProduct(BaseModel):
    """Common structure that every extracted listing is normalized into."""

    source_url: str
    product_name: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    delivery_charge: Optional[float] = None
    seller_name: Optional[str] = None
    seller_rating: Optional[float] = None       # Merchant/seller quality rating (0-5)
    customer_rating: Optional[float] = None     # Product review rating from buyers (0-5)
    customer_rating_count: Optional[int] = None # Number of customer reviews
    warranty: Optional[str] = None
    condition: Optional[str] = None
    availability: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    specifications: Dict[str, Any] = Field(default_factory=dict)
    raw_source: Optional[str] = None
    extraction_notes: List[str] = Field(default_factory=list)


class MatchResult(BaseModel):
    is_match: bool
    confidence: float
    reason: str


class RankedDeal(BaseModel):
    rank: int
    listing_index: int
    product_name: Optional[str] = None
    seller_name: Optional[str] = None
    price: Optional[float] = None
    delivery_charge: Optional[float] = None
    effective_price: Optional[float] = None
    price_score: float
    seller_score: float
    customer_rating_score: float
    warranty_score: float
    condition_score: float
    final_score: float


class Recommendation(BaseModel):
    best_listing_index: Optional[int] = None
    product_name: Optional[str] = None
    seller_name: Optional[str] = None
    effective_price: Optional[float] = None
    savings: Optional[float] = None
    explanation: str
    advantages: List[str] = Field(default_factory=list)
    disadvantages: List[str] = Field(default_factory=list)


class CompareUrlsResponse(BaseModel):
    listing_count: int
    listings: List[NormalizedProduct]
    comparisons: List[MatchResult]
    matched_listing_count: int
    ranked_deals: List[RankedDeal]
    recommendation: Optional[Recommendation] = None


class ErrorResponse(BaseModel):
    detail: str
