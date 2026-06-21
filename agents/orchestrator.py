"""Orchestrator: dispatches requests to category specialists and synthesizes results."""
from typing import Type

from agents.analysis.negotiation_brief import NegotiationBriefAgent
from agents.base import BaseAgent
from agents.category.appliances import AppliancesAgent
from agents.category.av import AVAgent
from agents.category.back_of_house import BackOfHouseAgent
from agents.category.bathroom import BathroomAgent
from agents.category.generalist import GeneralistAgent
from agents.research.hotel_benchmark import HotelBenchmarkAgent
from core.data_loader import get_category_weights
from core.models import Product, ResearchRequest, ResearchResult
from core.scoring import ScoreWeights, rank_products
from scraping.client import PoliteClient


class OrchestratorAgent(BaseAgent):
    """Central dispatcher that coordinates all specialist and analysis agents."""

    name = "orchestrator"

    CATEGORY_MAP = {
        # Appliances
        "hairdryer": AppliancesAgent,
        "minibar": AppliancesAgent,
        "safe": AppliancesAgent,
        "kettle": AppliancesAgent,
        "iron": AppliancesAgent,
        "fridge": AppliancesAgent,
        # AV
        "speaker": AVAgent,
        "television": AVAgent,
        "tv": AVAgent,
        # Bathroom
        "dispenser": BathroomAgent,
        "towel": BathroomAgent,
        "toiletries": BathroomAgent,
        # Back of house
        "cooking": BackOfHouseAgent,
        "dishwashing": BackOfHouseAgent,
        "laundry": BackOfHouseAgent,
        "housekeeping": BackOfHouseAgent,
        "small_equipment": BackOfHouseAgent,
        # General
        "faucet": GeneralistAgent,
        "shower": GeneralistAgent,
        "telephone": GeneralistAgent,
        "wifi": GeneralistAgent,
        "projector": GeneralistAgent,
        "furniture": GeneralistAgent,
    }

    BROADER_CATEGORY_MAP = {
        "appliances": AppliancesAgent,
        "av": AVAgent,
        "bathroom": BathroomAgent,
        "back_of_house": BackOfHouseAgent,
        "general": GeneralistAgent,
    }

    def __init__(self, client: PoliteClient | None = None):
        super().__init__(client)
        self.hotel_benchmark_agent = HotelBenchmarkAgent(client)
        self.negotiation_agent = NegotiationBriefAgent(client)

    def _resolve_specialist(self, category: str) -> Type[BaseAgent]:
        key = category.lower().strip()
        if key in self.CATEGORY_MAP:
            return self.CATEGORY_MAP[key]
        if key in self.BROADER_CATEGORY_MAP:
            return self.BROADER_CATEGORY_MAP[key]
        # Fallback to generalist for unknown categories
        return GeneralistAgent

    def _apply_budget_filter(
        self, products: list[Product], budget: float | None
    ) -> list[Product]:
        if budget is None or budget <= 0:
            return products
        return [p for p in products if p.effective_price is None or p.effective_price <= budget * 1.25]

    def run(self, request: ResearchRequest) -> ResearchResult:
        specialist_cls = self._resolve_specialist(request.category)
        specialist = specialist_cls(self.client)

        # Gather products
        products = specialist.run(request)
        products = self._apply_budget_filter(products, request.budget_per_unit_eur)

        # Rank using category-specific weights
        weights_dict = get_category_weights(specialist.category_key)
        weights = ScoreWeights.from_dict(weights_dict) if weights_dict else None
        ranked = rank_products(products, weights=weights)

        # Hotel benchmarks
        benchmarks = self.hotel_benchmark_agent.find_benchmarks(
            category=specialist.category_key, subcategory=request.category
        )

        # Negotiation briefs for top 3 products
        briefs = []
        for product in ranked[:3]:
            briefs.append(
                self.negotiation_agent.generate(product, alternatives=ranked[:5])
            )

        return ResearchResult(
            request=request,
            products=ranked,
            hotel_benchmarks=benchmarks,
            negotiation_briefs=briefs,
        )
