"""MatchingService

Decides whether two normalized product listings represent the same (or
close enough) product so that comparing their prices is meaningful. Uses
simple, transparent text-similarity heuristics over name/brand/model so
it stays generic across any e-commerce website - no site-specific rules.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import List

from app.schemas.product import MatchResult, NormalizedProduct

STOPWORDS = {
    "the", "a", "an", "for", "with", "and", "of", "in", "on", "new",
    "official", "genuine", "pack", "combo", "set",
}


class MatchingService:
    def compare_all(self, listings: List[NormalizedProduct]) -> List[MatchResult]:
        """Pairwise-compare every listing against listing[0] (the
        reference) so the frontend gets a simple linear list of
        comparisons alongside the ranked table."""
        results: List[MatchResult] = []
        if not listings:
            return results

        reference = listings[0]
        for other in listings[1:]:
            results.append(self.compare_pair(reference, other))
        return results

    def compare_pair(self, a: NormalizedProduct, b: NormalizedProduct) -> MatchResult:
        if not a.product_name or not b.product_name:
            return MatchResult(
                is_match=False,
                confidence=0.0,
                reason="Not enough product information was extracted to compare these listings.",
            )

        name_score = self._similarity(a.product_name, b.product_name)
        brand_score = self._similarity(a.brand, b.brand) if a.brand and b.brand else None
        model_score = self._similarity(a.model, b.model) if a.model and b.model else None

        weighted_scores = [(name_score, 0.6)]
        if brand_score is not None:
            weighted_scores.append((brand_score, 0.25))
        if model_score is not None:
            weighted_scores.append((model_score, 0.15))

        total_weight = sum(w for _, w in weighted_scores)
        confidence = sum(score * w for score, w in weighted_scores) / total_weight
        confidence = round(min(max(confidence, 0.0), 1.0), 2)

        is_match = confidence >= 0.55
        if brand_score is not None and brand_score < 0.4:
            is_match = False
            confidence = min(confidence, 0.4)

        if is_match:
            reason = "The listings appear to describe the same or a very similar product."
        else:
            reason = "The listings are different products."

        return MatchResult(is_match=is_match, confidence=confidence, reason=reason)

    # ------------------------------------------------------------------
    @staticmethod
    def _tokenize(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        tokens = [t for t in text.split() if t not in STOPWORDS]
        return " ".join(sorted(tokens))

    def _similarity(self, a: str, b: str) -> float:
        norm_a = self._tokenize(a)
        norm_b = self._tokenize(b)
        if not norm_a or not norm_b:
            return 0.0
        return SequenceMatcher(None, norm_a, norm_b).ratio()
