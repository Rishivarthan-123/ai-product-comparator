"""DealScoringService

Scoring weights (updated to include customer rating):

    effective_price = price + delivery_charge

    price_score           = lowest_effective_price / current_effective_price * 100
    customer_rating_score = customer_rating / 5 * 100
    seller_score          = seller_rating / 5 * 100
    warranty_score        = tiered (2yr=100, 1yr=90, 6mo=70, 3mo=50, other=40, unknown=0)
    condition_score       = new=100, refurbished=70, used=50, unknown=0

    final_score = price*0.40 + customer_rating*0.25 + seller*0.15 + warranty*0.12 + condition*0.08
"""

from __future__ import annotations

import re
from typing import List, Optional

from app.schemas.product import NormalizedProduct, RankedDeal

CONDITION_SCORES = {
    "new": 100.0,
    "refurbished": 70.0,
    "used": 50.0,
    "unknown": 0.0,
}


class DealScoringService:
    def score_all(self, listings: List[NormalizedProduct]) -> List[RankedDeal]:
        effective_prices = [self.effective_price(l) for l in listings]
        valid_prices = [p for p in effective_prices if p is not None and p > 0]
        lowest_price = min(valid_prices) if valid_prices else None

        deals: List[RankedDeal] = []
        for index, listing in enumerate(listings):
            effective_price = effective_prices[index]
            price_score = self._price_score(effective_price, lowest_price)
            customer_rating_score = self._customer_rating_score(listing.customer_rating)
            seller_score = self._seller_score(listing.seller_rating)
            warranty_score = self._warranty_score(listing.warranty)
            condition_score = self._condition_score(listing.condition)

            final_score = round(
                price_score           * 0.40
                + customer_rating_score * 0.25
                + seller_score          * 0.15
                + warranty_score        * 0.12
                + condition_score       * 0.08,
                2,
            )

            deals.append(
                RankedDeal(
                    rank=0,
                    listing_index=index,
                    product_name=listing.product_name,
                    seller_name=listing.seller_name,
                    price=listing.price,
                    delivery_charge=listing.delivery_charge,
                    effective_price=effective_price,
                    price_score=price_score,
                    customer_rating_score=customer_rating_score,
                    seller_score=seller_score,
                    warranty_score=warranty_score,
                    condition_score=condition_score,
                    final_score=final_score,
                )
            )
        return self.rank_deals(deals)

    # ------------------------------------------------------------------
    @staticmethod
    def effective_price(listing: NormalizedProduct) -> Optional[float]:
        if listing.price is None:
            return None
        delivery = listing.delivery_charge if listing.delivery_charge is not None else 0.0
        return round(listing.price + delivery, 2)

    @staticmethod
    def _price_score(effective_price: Optional[float], lowest_price: Optional[float]) -> float:
        if effective_price is None or lowest_price is None or effective_price <= 0:
            return 0.0
        return round((lowest_price / effective_price) * 100, 2)

    @staticmethod
    def _customer_rating_score(customer_rating: Optional[float]) -> float:
        """Convert a 0-5 product review rating into a 0-100 score."""
        if customer_rating is None:
            return 0.0
        return round((customer_rating / 5) * 100, 2)

    @staticmethod
    def _seller_score(seller_rating: Optional[float]) -> float:
        if seller_rating is None:
            return 0.0
        return round((seller_rating / 5) * 100, 2)

    @staticmethod
    def _warranty_score(warranty: Optional[str]) -> float:
        if not warranty:
            return 0.0
        text = warranty.lower()
        years_match = re.search(r"(\d+(\.\d+)?)\s*year", text)
        months_match = re.search(r"(\d+)\s*month", text)
        years = float(years_match.group(1)) if years_match else None
        months = float(months_match.group(1)) if months_match else None
        if years is None and months is not None:
            years = months / 12
        if years is not None:
            if years >= 2:
                return 100.0
            if years >= 1:
                return 90.0
            if months is not None and months >= 6:
                return 70.0
            if months is not None and months >= 3:
                return 50.0
        return 40.0

    @staticmethod
    def _condition_score(condition: Optional[str]) -> float:
        if not condition:
            return CONDITION_SCORES["unknown"]
        return CONDITION_SCORES.get(condition.lower(), CONDITION_SCORES["unknown"])

    # ------------------------------------------------------------------
    @staticmethod
    def rank_deals(deals: List[RankedDeal]) -> List[RankedDeal]:
        ordered = sorted(deals, key=lambda d: d.final_score, reverse=True)
        for position, deal in enumerate(ordered, start=1):
            deal.rank = position
        return sorted(ordered, key=lambda d: d.listing_index)
