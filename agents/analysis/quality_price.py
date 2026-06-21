"""Quality-price scoring agent."""
from typing import Any, Dict

from agents.base import BaseAgent
from core.models import Product, ResearchRequest, ReviewSignals


class QualityPriceAgent(BaseAgent):
    """Compute a quality score from specs, brand tier, warranty, and reviews."""

    name = "quality_price"

    # Brand tier scores (luxury = higher base quality)
    TIER_SCORES = {
        "ultra_luxury": 90,
        "established_luxury": 78,
        "commercial_specialist": 72,
        "unknown": 55,
    }

    def score_product(
        self,
        product: Product,
        brand_tier: str = "unknown",
        review_signals: ReviewSignals | None = None,
    ) -> Dict[str, Any]:
        base = self.TIER_SCORES.get(brand_tier, self.TIER_SCORES["unknown"])

        # Spec completeness
        spec_count = len(product.specs)
        spec_score = min(spec_count * 6, 25)

        # Warranty length (commercial)
        warranty = product.warranty_years or 0
        warranty_score = min(warranty * 8, 20)

        # Review sentiment
        review_signals = review_signals or product.review_signals
        sentiment_score = 0
        if review_signals:
            sentiment_score = max(0, min(15, (review_signals.avg_sentiment + 1) * 7.5))
            if review_signals.durability_mentions > 0:
                sentiment_score += min(5, review_signals.durability_mentions)

        quality_score = base * 0.50 + spec_score + warranty_score + sentiment_score
        quality_score = max(0, min(100, quality_score))

        # Value score is computed later by the scoring engine relative to peers
        return {
            "quality_score": round(quality_score, 1),
            "breakdown": {
                "base_brand_tier": base,
                "spec_completeness": spec_score,
                "warranty": warranty_score,
                "review_sentiment": round(sentiment_score, 1),
            },
        }

    def run(self, request: ResearchRequest) -> Dict[str, Any]:
        return {"quality_score": 50, "breakdown": {}}
