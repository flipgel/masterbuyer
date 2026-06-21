"""Base category specialist with shared enrichment logic."""
from typing import Any, Dict, List

from agents.analysis.compliance import ComplianceAgent
from agents.analysis.exclusivity import ExclusivityAgent
from agents.analysis.quality_price import QualityPriceAgent
from agents.analysis.supplier_cross_check import SupplierCrossCheckAgent
from agents.analysis.tco import TCOAgent
from agents.base import BaseAgent
from agents.research.review_sentiment import ReviewSentimentAgent
from core.data_loader import load_category_taxonomy, load_sample_products
from core.models import Product, ResearchRequest, ReviewSignals, Supplier


class CategoryAgent(BaseAgent):
    """Specialist that knows how to evaluate products in a category."""

    category_key: str = ""

    def __init__(self, client=None):
        super().__init__(client)
        self.taxonomy = load_category_taxonomy()
        self.all_products = load_sample_products()
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

    def _dict_to_product(self, data: Dict[str, Any]) -> Product:
        review = ReviewSignals(**data.get("review_signals", {}))
        supplier_data = data.get("supplier")
        supplier = None
        if supplier_data:
            supplier = Supplier(**supplier_data)
        else:
            # Try to attach a supplier from the index
            suppliers = self.supplier_agent.find_suppliers_for_brand(data["brand"])
            if suppliers:
                supplier = suppliers[0]

        return Product(
            id=data["id"],
            name=data["name"],
            brand=data["brand"],
            category=data["category"],
            subcategory=data["subcategory"],
            specs=data.get("specs", {}),
            list_price_eur=data.get("list_price_eur"),
            estimated_price_eur=data.get("estimated_price_eur"),
            supplier=supplier,
            source_url=data.get("source_url"),
            availability_weeks=data.get("availability_weeks"),
            warranty_years=data.get("warranty_years"),
            certifications=data.get("certifications", []),
            hotel_usage=data.get("hotel_usage", []),
            review_signals=review,
            pros=data.get("pros", []),
            cons=data.get("cons", []),
        )

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

    def get_products(self, requested_category: str | None = None) -> List[Product]:
        """Load seed products for this category.

        If requested_category looks like a subcategory (e.g. 'faucet' under general),
        filter by subcategory as well.
        """
        items = [p for p in self.all_products if p["category"] == self.category_key]
        if requested_category and requested_category != self.category_key:
            items = [p for p in items if p["subcategory"] == requested_category]
        return [self._dict_to_product(p) for p in items]

    def run(self, request: ResearchRequest) -> List[Product]:
        products = self.get_products(request.category)
        return [self.enrich_product(p) for p in products]
