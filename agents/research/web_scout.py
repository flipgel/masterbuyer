"""Web scouting agent: searches public web for product information."""
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from agents.base import BaseAgent
from core.models import ResearchRequest
from scraping.extractors import extract_manufacturer_specs


class WebScoutAgent(BaseAgent):
    """Find product pages and extract specs/prices from manufacturer sites."""

    name = "web_scout"

    # Known search URL builders — no paid API required.
    SEARCH_ENGINES = {
        "google": lambda q: f"https://www.google.com/search?q={quote_plus(q)}",
        "bing": lambda q: f"https://www.bing.com/search?q={quote_plus(q)}",
        "duckduckgo": lambda q: f"https://duckduckgo.com/html/?q={quote_plus(q)}",
    }

    def build_search_urls(self, query: str) -> Dict[str, str]:
        return {name: fn(query) for name, fn in self.SEARCH_ENGINES.items()}

    def build_manufacturer_search_query(
        self, brand: str, product_name: str, subcategory: str
    ) -> str:
        return f"{brand} {product_name} {subcategory} specifications price"

    def scout_product(
        self,
        brand: str,
        product_name: str,
        subcategory: str,
        urls_to_try: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Fetch product pages and extract specs. Returns best-effort data."""
        urls = urls_to_try or []
        aggregated = {
            "brand": brand,
            "product_name": product_name,
            "subcategory": subcategory,
            "search_urls": self.build_search_urls(
                self.build_manufacturer_search_query(brand, product_name, subcategory)
            ),
            "fetched_pages": [],
            "price_candidates": [],
            "specs": {},
            "description": "",
        }

        for url in urls:
            try:
                result = self.client.get(url, use_cache=True)
                if result.status_code == 200:
                    extracted = extract_manufacturer_specs(result)
                    aggregated["fetched_pages"].append(
                        {
                            "url": extracted.get("source_url"),
                            "title": extracted.get("name"),
                            "status": result.status_code,
                        }
                    )
                    aggregated["price_candidates"].extend(extracted.get("price_candidates", []))
                    if extracted.get("description"):
                        aggregated["description"] += " " + extracted["description"]
                    for table in extracted.get("tables", []):
                        aggregated["specs"].update(table)
            except Exception as e:
                aggregated["fetched_pages"].append(
                    {"url": url, "status": "error", "error": str(e)}
                )

        # Deduplicate price candidates
        seen = set()
        unique_prices = []
        for price in aggregated["price_candidates"]:
            rounded = round(price, 2)
            if rounded not in seen:
                seen.add(rounded)
                unique_prices.append(rounded)
        aggregated["price_candidates"] = sorted(unique_prices)
        aggregated["description"] = aggregated["description"].strip()
        return aggregated

    def run(self, request: ResearchRequest) -> Dict[str, Any]:
        return self.scout_product(
            brand="",
            product_name=request.design_brief,
            subcategory=request.category,
        )
