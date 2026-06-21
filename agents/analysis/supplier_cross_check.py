"""Supplier cross-check agent: validate supplier coverage and certifications."""
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from core.data_loader import load_suppliers
from core.models import Product, ResearchRequest, Supplier
from rapidfuzz import fuzz


class SupplierCrossCheckAgent(BaseAgent):
    """Match products to suppliers and score supplier reliability."""

    name = "supplier_cross_check"

    def __init__(self, client=None):
        super().__init__(client)
        self.suppliers = load_suppliers()

    def find_suppliers_for_brand(self, brand: str) -> List[Supplier]:
        matches = []
        for s in self.suppliers:
            carried = s.get("brands_carried", [])
            if any(brand.lower() == c.lower() or brand.lower() in c.lower() for c in carried):
                matches.append(self._dict_to_supplier(s))
        return matches

    def find_suppliers_for_category(self, category: str, subcategory: str) -> List[Supplier]:
        matches = []
        for s in self.suppliers:
            specialties = s.get("specialties", [])
            if category in specialties or subcategory in specialties:
                matches.append(self._dict_to_supplier(s))
        return matches

    def _dict_to_supplier(self, data: Dict[str, Any]) -> Supplier:
        return Supplier(
            name=data["name"],
            country=data["country"],
            website=data["website"],
            is_authorized=True,
            service_countries=data.get("service_countries", []),
            moq=data.get("moq"),
            certifications=data.get("certifications", []),
            notes=data.get("notes", ""),
        )

    def score_supplier(self, supplier: Supplier, target_country: str) -> Dict[str, Any]:
        score = 50
        reasons = []
        if target_country and target_country.upper() in [c.upper() for c in supplier.service_countries]:
            score += 25
            reasons.append(f"Services target country {target_country}")
        else:
            reasons.append("No confirmed service coverage in target country")
        if supplier.certifications:
            score += 15
            reasons.append(f"Holds certifications: {', '.join(supplier.certifications)}")
        if supplier.is_authorized:
            score += 10
            reasons.append("Listed as authorized/curated distributor")
        return {"score": min(score, 100), "reasons": reasons}

    def run(self, request: ResearchRequest) -> List[Supplier]:
        return self.find_suppliers_for_category(request.category, "")
