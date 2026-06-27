"""Base category specialist with shared enrichment logic."""
from typing import List

from agents.analysis.compliance import ComplianceAgent
from agents.analysis.exclusivity import ExclusivityAgent
from agents.analysis.quality_price import QualityPriceAgent
from agents.analysis.supplier_cross_check import SupplierCrossCheckAgent
from agents.analysis.tco import TCOAgent
from agents.base import BaseAgent
from agents.research.live_search import LiveSearchAgent
from agents.research.review_sentiment import ReviewSentimentAgent
from core.data_loader import load_category_taxonomy
from core.models import Product, ResearchRequest


class CategoryAgent(BaseAgent):
    """Specialist that knows how to evaluate products in a category."""

    category_key: str = ""

    def __init__(self, client=None):
        super().__init__(client)
        self.taxonomy = load_category_taxonomy()
        self.live_search_agent = LiveSearchAgent(client)
        self.exclusivity_agent = ExclusivityAgent(client)
        self.quality_agent = QualityPriceAgent(client)
        self.tco_agent = TCOAgent(client)
        self.compliance_agent = ComplianceAgent(client)
        self.supplier_agent = SupplierCrossCheckAgent(client)
        self.review_agent = ReviewSentimentAgent(client)

    def _find_brand_tier(self, brand: str, category: str) -> str:
        cats = self.taxonomy.get("categories", {})
        tiers = cats.get(category, {}).get("brand_tiers", {})
        for tier, brands in tiers.items():
            if brand in brands:
                return tier
        return "unknown"

    def enrich_product(self, product: Product) -> Product:
        """Run all analysis agents on a product and populate scores."""
        # Exclusivity / rarity
        exc = self.exclusivity_agent.score_brand(product.brand, product.hotel_usage)
        product.rarity_score = exc["rarity_score"]
        product.exclusivity_score = exc["exclusivity_score"]

        # Quality
        tier = self._find_brand_tier(product.brand, product.category)
        q = self.quality_agent.score_product(product, brand_tier=tier)
        product.quality_score = q["quality_score"]

        # TCO
        tco = self.tco_agent.estimate(product)
        product.tco_10yr_eur = tco.get("tco_10yr_eur")

        # Compliance
        comp = self.compliance_agent.check_product(product)
        product.compliance_score = comp["compliance_score"]
        product.compliance_flags = comp["flags"]

        # Review signals (if none provided, infer from pros/cons)
        if not product.review_signals.source_count:
            text = " ".join(product.pros + product.cons)
            product.review_signals = self.review_agent.analyze(text)

        return product

    def get_products(self, request: ResearchRequest) -> List[Product]:
        """Live-search for products in this category.

        `request.category` may be a subcategory (e.g. 'faucet' under general); it's
        passed through as the subcategory hint for search query building.
        """
        query = request.query or request.design_brief or request.category
        return self.live_search_agent.find_products(
            query=query, category=self.category_key, subcategory=request.category,
            brand_mode=request.brand_mode,
        )

    def run(self, request: ResearchRequest) -> List[Product]:
        products = self.get_products(request)
        return [self.enrich_product(p) for p in products]
