"""Composite scoring engine for products and suppliers."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.config import DEFAULT_SCORE_WEIGHTS
from core.models import Product


@dataclass
class ScoreWeights:
    rarity: float = 0.20
    quality: float = 0.25
    value: float = 0.20
    tco: float = 0.15
    exclusivity: float = 0.15
    compliance: float = 0.05

    def validate(self) -> None:
        total = sum([self.rarity, self.quality, self.value, self.tco, self.exclusivity, self.compliance])
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Score weights must sum to 1.0, got {total}")

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> "ScoreWeights":
        return cls(
            rarity=d.get("rarity", 0.20),
            quality=d.get("quality", 0.25),
            value=d.get("value", 0.20),
            tco=d.get("tco", 0.15),
            exclusivity=d.get("exclusivity", 0.15),
            compliance=d.get("compliance", 0.05),
        )


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def compute_value_score(product: Product, category_median_price: Optional[float]) -> float:
    """Higher quality per euro yields a higher value score."""
    price = product.effective_price
    if price is None or price <= 0:
        # No price: value is quality discounted slightly
        return clamp(product.quality_score * 0.75)
    reference = category_median_price if category_median_price and category_median_price > 0 else price
    price_ratio = reference / price
    score = product.quality_score * min(price_ratio, 2.0)
    return clamp(score)


def compute_tco_score(product: Product) -> float:
    """Lower 10-year TCO relative to price yields a higher score."""
    price = product.effective_price
    if price is None or price <= 0 or product.tco_10yr_eur is None:
        # Cannot compute TCO; fall back to quality + warranty proxy
        warranty_boost = min((product.warranty_years or 0) * 3, 15)
        return clamp(product.quality_score * 0.7 + warranty_boost)
    tco_ratio = price / product.tco_10yr_eur
    # Ratio 1.0 (no extra cost) => high score; lower ratio => lower score
    score = 50 + 50 * clamp(tco_ratio * 2, 0, 1)
    return clamp(score)


def compute_overall_score(product: Product, weights: ScoreWeights) -> float:
    """Weighted composite of all individual scores."""
    weights.validate()
    overall = (
        product.rarity_score * weights.rarity +
        product.quality_score * weights.quality +
        product.value_score * weights.value +
        product.tco_score * weights.tco +
        product.exclusivity_score * weights.exclusivity +
        product.compliance_score * weights.compliance
    )
    return clamp(overall)


def rank_products(products: List[Product], weights: Optional[ScoreWeights] = None) -> List[Product]:
    """Recompute value/TCO/overall scores and return products sorted by overall score."""
    if weights is None:
        weights = ScoreWeights.from_dict(DEFAULT_SCORE_WEIGHTS)

    prices = [p.effective_price for p in products if p.effective_price is not None]
    median_price = sorted(prices)[len(prices) // 2] if prices else None

    for product in products:
        product.value_score = compute_value_score(product, median_price)
        product.tco_score = compute_tco_score(product)
        product.overall_score = compute_overall_score(product, weights)

    return sorted(products, key=lambda p: p.overall_score, reverse=True)


def score_to_grade(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "F"
