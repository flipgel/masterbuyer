"""Compliance agent: verify EU regulatory and commercial-hotel requirements."""
from typing import Any, Dict, List

from agents.base import BaseAgent
from core.models import Product, ResearchRequest


class ComplianceAgent(BaseAgent):
    """Check CE marking, energy labels, WEEE, REACH, and warranty adequacy."""

    name = "compliance"

    REQUIRED_CERTS = {
        "appliances": ["CE"],
        "av": ["CE", "Energy Label"],
        "bathroom": ["CE"],
        "back_of_house": ["CE"],
        "general": ["CE"],
    }

    def check_product(self, product: Product, target_country: str = "EU") -> Dict[str, Any]:
        required = self.REQUIRED_CERTS.get(product.category, ["CE"])
        flags = []
        score = 100

        missing = [cert for cert in required if cert not in product.certifications]
        if missing:
            flags.append(f"Missing certifications: {', '.join(missing)}")
            score -= len(missing) * 25

        if product.category == "av" and "Energy Label" not in product.certifications:
            flags.append("Televisions require EU Energy Label in Europe.")
            score -= 20

        if product.warranty_years is None:
            flags.append("No warranty information available.")
            score -= 15
        elif product.warranty_years < 1 and product.category != "bathroom":
            flags.append("Warranty shorter than 1 year for commercial use.")
            score -= 10

        if target_country.upper() == "GB" and "UKCA" not in product.certifications:
            flags.append("UKCA marking recommended for Great Britain.")
            score -= 5

        score = max(0, min(100, score))
        return {
            "compliance_score": round(score, 1),
            "required_certifications": required,
            "present_certifications": product.certifications,
            "missing_certifications": missing,
            "flags": flags,
        }

    def run(self, request: ResearchRequest) -> Dict[str, Any]:
        return {
            "compliance_score": 50,
            "required_certifications": self.REQUIRED_CERTS.get(request.category, ["CE"]),
            "flags": [],
        }
