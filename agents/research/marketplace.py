"""B2B marketplace agent: generate search URLs and scrape simple listings."""
from typing import Any, Dict, List
from urllib.parse import quote_plus

from agents.base import BaseAgent
from core.models import ResearchRequest


class MarketplaceAgent(BaseAgent):
    """Search hospitality B2B marketplaces without paid APIs."""

    name = "marketplace"

    MARKETPLACES = {
        "alibaba": lambda q: f"https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&CatId=&SearchText={quote_plus(q)}",
        "faire": lambda q: f"https://www.faire.com/search?q={quote_plus(q)}",
        "nisbets": lambda q: f"https://www.nisbets.co.uk/search?text={quote_plus(q)}",
        "horecatraders": lambda q: f"https://www.horecatraders.com/search?q={quote_plus(q)}",
        "google_shopping": lambda q: f"https://www.google.com/search?tbm=shop&q={quote_plus(q)}",
    }

    def build_search_urls(self, query: str) -> Dict[str, str]:
        return {name: fn(query) for name, fn in self.MARKETPLACES.items()}

    def search(self, brand: str, product_name: str, subcategory: str) -> Dict[str, Any]:
        query = f"{brand} {product_name} {subcategory}"
        return {
            "query": query,
            "urls": self.build_search_urls(query),
            "note": "Marketplace scraping is intentionally light to respect rate limits; use the generated URLs for manual verification or RFQ outreach.",
        }

    def run(self, request: ResearchRequest) -> Dict[str, Any]:
        return self.search("", request.design_brief, request.category)
