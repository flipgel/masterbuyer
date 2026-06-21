"""Negotiation brief agent: generate supplier negotiation one-pagers."""
from typing import Any, Dict, List

from agents.base import BaseAgent
from core.models import NegotiationBrief, Product, ResearchRequest, Supplier


class NegotiationBriefAgent(BaseAgent):
    """Create negotiation briefs using market position and alternatives."""

    name = "negotiation_brief"

    def generate(
        self,
        product: Product,
        alternatives: List[Product],
        supplier: Supplier | None = None,
    ) -> NegotiationBrief:
        alt_names = [f"{p.brand} {p.name}" for p in alternatives if p.id != product.id][:3]

        leverage = []
        if alternatives:
            leverage.append(f"{len(alternatives)} comparable alternatives identified")
        if product.hotel_usage:
            leverage.append(f"Used by {', '.join(product.hotel_usage[:2])}")
        if product.exclusivity_score > 70:
            leverage.append("Brand has strong exclusivity — limited negotiation room on price")
        else:
            leverage.append("Brand is widely available — negotiate volume discount")
        if product.warranty_years and product.warranty_years >= 2:
            leverage.append("Warranty is competitive; request extended coverage or spare-parts commitment")

        target_price = None
        if product.effective_price:
            if product.exclusivity_score > 75:
                target_price = round(product.effective_price * 0.95, 2)
            elif product.value_score > 75:
                target_price = round(product.effective_price * 0.90, 2)
            else:
                target_price = round(product.effective_price * 0.85, 2)

        position = "premium / niche" if product.exclusivity_score > 70 else "mainstream premium"
        if product.quality_score > 85 and product.value_score > 70:
            position = "best value in premium segment"
        elif product.quality_score > 85 and product.value_score < 60:
            position = "quality leader, expensive"

        suggested_terms = [
            "Request all-inclusive landed price for EU delivery",
            "Ask for extended payment terms (e.g., 30% deposit, 70% on delivery)",
            "Negotiate training, installation, and commissioning if applicable",
            "Secure guaranteed lead times with penalty clauses",
            "Ask for sample/evaluation unit before full order",
        ]

        return NegotiationBrief(
            supplier_name=supplier.name if supplier else product.brand,
            product_name=f"{product.brand} {product.name}",
            market_position=position,
            alternatives=alt_names,
            leverage_points=leverage,
            target_price_eur=target_price,
            suggested_terms=suggested_terms,
        )

    def run(self, request: ResearchRequest) -> Dict[str, Any]:
        return {
            "note": "Negotiation briefs are generated per shortlisted product after scoring.",
        }
