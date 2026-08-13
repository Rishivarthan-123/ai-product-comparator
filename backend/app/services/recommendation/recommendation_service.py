"""RecommendationService

Picks the highest ranked deal and produces a plain-English explanation
including customer rating, seller quality, price, warranty and condition.
"""

from __future__ import annotations

from typing import List, Optional

from app.schemas.product import NormalizedProduct, RankedDeal, Recommendation


class RecommendationService:
    def recommend(
        self, listings: List[NormalizedProduct], ranked_deals: List[RankedDeal]
    ) -> Optional[Recommendation]:
        if not ranked_deals:
            return None

        best = min(ranked_deals, key=lambda d: d.rank)
        best_listing = listings[best.listing_index] if best.listing_index < len(listings) else None

        others = [d for d in ranked_deals if d.listing_index != best.listing_index]
        savings = None
        if others and best.effective_price is not None:
            comparable = [d.effective_price for d in others if d.effective_price is not None]
            if comparable:
                next_best_price = min(comparable)
                if next_best_price > best.effective_price:
                    savings = round(next_best_price - best.effective_price, 2)

        advantages = self._build_advantages(best, others, best_listing)
        disadvantages = self._build_disadvantages(best, best_listing)

        subject = self._subject_label(best, listings)
        explanation = self._build_explanation(subject, advantages)

        return Recommendation(
            best_listing_index=best.listing_index,
            product_name=best.product_name,
            seller_name=best.seller_name,
            effective_price=best.effective_price,
            savings=savings,
            explanation=explanation,
            advantages=advantages,
            disadvantages=disadvantages,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _subject_label(best: RankedDeal, listings: List[NormalizedProduct]) -> str:
        if best.product_name:
            return best.product_name
        ordinal = ["first", "second", "third", "fourth", "fifth", "sixth"]
        idx = best.listing_index
        label = ordinal[idx] if idx < len(ordinal) else f"listing {idx + 1}"
        return f"The {label} listing"

    @staticmethod
    def _build_advantages(
        best: RankedDeal,
        others: List[RankedDeal],
        best_listing: Optional[NormalizedProduct],
    ) -> List[str]:
        advantages: List[str] = []

        if others:
            # Price
            comparable_prices = [d.effective_price for d in others if d.effective_price is not None]
            if best.effective_price is not None and comparable_prices and best.effective_price <= min(comparable_prices):
                advantages.append("the lowest effective price (including delivery)")

            # Customer rating
            comparable_cr = [d.customer_rating_score for d in others]
            if best.customer_rating_score > 0 and comparable_cr and best.customer_rating_score > max(comparable_cr):
                cr = best_listing.customer_rating if best_listing else None
                count = best_listing.customer_rating_count if best_listing else None
                cr_str = f"{cr}/5" if cr else "the highest"
                count_str = f" from {count:,} reviews" if count else ""
                advantages.append(f"the best customer rating ({cr_str}{count_str})")

            # Seller rating
            comparable_seller = [d.seller_score for d in others]
            if best.seller_score > 0 and comparable_seller and best.seller_score > max(comparable_seller):
                advantages.append("a higher rated seller")

            # Warranty
            comparable_warranty = [d.warranty_score for d in others]
            if best.warranty_score > 0 and comparable_warranty and best.warranty_score > max(comparable_warranty):
                advantages.append("a longer or stronger warranty")

            # Condition
            comparable_condition = [d.condition_score for d in others]
            if best.condition_score > 0 and comparable_condition and best.condition_score > max(comparable_condition):
                advantages.append("better product condition")

        if not advantages and best.final_score > 0:
            advantages.append("the best overall balance of price, customer rating, seller quality, warranty, and condition")

        return advantages

    @staticmethod
    def _build_disadvantages(best: RankedDeal, best_listing: Optional[NormalizedProduct]) -> List[str]:
        disadvantages: List[str] = []
        if best_listing is None:
            return disadvantages
        if best.customer_rating_score == 0:
            disadvantages.append("Customer review rating could not be determined for this listing.")
        if best.seller_score == 0:
            disadvantages.append("Seller rating could not be determined for this listing.")
        if best.warranty_score == 0:
            disadvantages.append("Warranty information could not be confirmed for this listing.")
        if best_listing.condition == "unknown":
            disadvantages.append("Product condition could not be confirmed for this listing.")
        return disadvantages

    @staticmethod
    def _build_explanation(subject: str, advantages: List[str]) -> str:
        if not advantages:
            return f"{subject} is the best overall deal based on the available information."
        if len(advantages) == 1:
            reason_text = advantages[0]
        elif len(advantages) == 2:
            reason_text = f"{advantages[0]} and {advantages[1]}"
        else:
            reason_text = ", ".join(advantages[:-1]) + f", and {advantages[-1]}"
        return f"{subject} is the best overall deal because it has {reason_text}."
