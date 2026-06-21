"""Exclusivity / rarity scoring agent."""
from typing import Any, Dict, List

from agents.base import BaseAgent
from agents.research.hotel_benchmark import HotelBenchmarkAgent
from core.data_loader import get_brand_rarity
from core.models import Product, ResearchRequest


class ExclusivityAgent(BaseAgent):
    """Score how rare or exclusive a brand/product is in the luxury hotel market."""

    name = "exclusivity"

    def __init__(self, client=None):
        super().__init__(client)
        self.benchmark_agent = HotelBenchmarkAgent(client)

    def score_brand(self, brand: str, hotel_usage: List[str]) -> Dict[str, float]:
        rarity_meta = get_brand_rarity(brand)
        presence = self.benchmark_agent.brand_presence_in_luxury_hotels(brand)

        global_presence = rarity_meta.get("global_presence", "medium")
        hotel_presence = rarity_meta.get("hotel_presence", "medium")
        boutique_coefficient = rarity_meta.get("boutique_coefficient", 0.5)

        presence_map = {"low": 0.2, "medium": 0.5, "high": 0.9}
        global_score = (1 - presence_map.get(global_presence, 0.5)) * 100
        hotel_score = (1 - presence_map.get(hotel_presence, 0.5)) * 100

        # Fewer luxury hotel mentions = higher rarity
        usage_penalty = min(presence["count"] * 8, 40)
        usage_rarity = max(0, 100 - usage_penalty)

        rarity_score = (
            global_score * 0.25
            + hotel_score * 0.25
            + usage_rarity * 0.30
            + boutique_coefficient * 100 * 0.20
        )
        rarity_score = max(0, min(100, rarity_score))

        # Exclusivity considers distribution limitation + boutique cachet
        exclusivity_score = (
            rarity_score * 0.50
            + boutique_coefficient * 100 * 0.30
            + (100 - min(presence["count"] * 10, 100)) * 0.20
        )
        exclusivity_score = max(0, min(100, exclusivity_score))

        return {
            "rarity_score": round(rarity_score, 1),
            "exclusivity_score": round(exclusivity_score, 1),
            "luxury_hotel_count": presence["count"],
            "boutique_coefficient": boutique_coefficient,
        }

    def run(self, request: ResearchRequest) -> Dict[str, Any]:
        # Default score for a generic request without a specific product
        return self.score_brand("", [])
