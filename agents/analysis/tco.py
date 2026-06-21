"""Total Cost of Ownership agent."""
from typing import Any, Dict, Optional

from agents.base import BaseAgent
from core.models import Product, ResearchRequest


class TCOAgent(BaseAgent):
    """Estimate 10-year total cost of ownership for a product."""

    name = "tco"

    # Default assumptions for luxury hotel use
    DEFAULT_LIFESPAN_YEARS = {
        "hairdryer": 5,
        "minibar": 10,
        "safe": 12,
        "kettle": 5,
        "iron": 6,
        "speaker": 8,
        "television": 7,
        "dispenser": 5,
        "towel": 3,
        "toiletries": 0,  # consumable
        "cooking": 12,
        "dishwashing": 10,
        "laundry": 10,
        "small_equipment": 8,
        "faucet": 15,
        "shower": 15,
        "telephone": 8,
        "wifi": 7,
        "projector": 8,
        "furniture": 12,
    }

    # Annual energy/maintenance estimate as % of purchase price
    ANNUAL_RUN_COST_PCT = {
        "hairdryer": 2,
        "minibar": 12,
        "safe": 1,
        "kettle": 5,
        "iron": 3,
        "speaker": 2,
        "television": 5,
        "dispenser": 1,
        "towel": 20,  # replacement
        "toiletries": 100,  # fully consumable
        "cooking": 4,
        "dishwashing": 6,
        "laundry": 8,
        "small_equipment": 5,
        "faucet": 1,
        "shower": 1,
        "telephone": 2,
        "wifi": 3,
        "projector": 6,
        "furniture": 2,
    }

    def estimate(
        self,
        product: Product,
        lifespan_years: Optional[int] = None,
        annual_run_cost_pct: Optional[float] = None,
    ) -> Dict[str, Any]:
        price = product.effective_price
        subcategory = product.subcategory

        if price is None or price <= 0:
            return {
                "tco_10yr_eur": None,
                "lifespan_years": self.DEFAULT_LIFESPAN_YEARS.get(subcategory, 8),
                "annual_energy_maintenance_eur": None,
                "replacement_cost_eur": None,
                "note": "Price unknown; TCO cannot be computed.",
            }

        life = lifespan_years or self.DEFAULT_LIFESPAN_YEARS.get(subcategory, 8)
        run_pct = annual_run_cost_pct or self.ANNUAL_RUN_COST_PCT.get(subcategory, 3)

        annual_run = price * (run_pct / 100)
        years_in_period = min(10, life)
        replacement_cycles = max(0, 10 // life - (1 if 10 % life == 0 else 0))
        replacement_cost = replacement_cycles * price
        tco = price + (annual_run * years_in_period) + replacement_cost

        return {
            "tco_10yr_eur": round(tco, 2),
            "lifespan_years": life,
            "annual_energy_maintenance_eur": round(annual_run, 2),
            "replacement_cost_eur": round(replacement_cost, 2),
            "note": f"Assumed {life}-year lifespan and {run_pct}% annual running cost.",
        }

    def run(self, request: ResearchRequest) -> Dict[str, Any]:
        return {"tco_10yr_eur": None, "note": "No product specified."}
