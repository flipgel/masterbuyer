"""Live search agent: finds real candidate products via the Serper.dev Search API.

Two complementary sources per query:
1. Google Shopping (via Serper) — gives name/price/link/source merchant directly,
   no need to scrape B2B sites (many of which are bot-walled or JS-only).
2. Organic search scoped to matched suppliers (`site:<domain>`) — finds manufacturer
   spec pages, which we then fetch and parse for extra detail when the site allows it.
   Sites that block scraping (Cloudflare, etc.) are simply skipped, not fatal.
"""
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from agents.analysis.supplier_cross_check import SupplierCrossCheckAgent
from agents.base import BaseAgent
from core.data_loader import get_all_known_brands, load_suppliers
from core.models import Product, ResearchRequest, Supplier
from scraping.extractors import extract_manufacturer_specs
from scraping.serper import OrganicResult, ShoppingResult, search_organic, search_shopping

MAX_SUPPLIERS = 6
SHOPPING_RESULTS = 10
ORGANIC_RESULTS_PER_SUPPLIER = 3
MIN_PLAUSIBLE_PRICE_EUR = 5.0

# Organic site search surfaces any page mentioning the query, including blog posts and
# buying guides — these have no real price and would otherwise pick up a stray number
# from the article body as a fake "price". Filter them out by URL/title signal.
NON_PRODUCT_SIGNALS = (
    "/blog/", "/news/", "/guide", "/guides/", "/article", "/press/",
    "how to ", "tips", "gift", "gifts", "ways to", "buying guide", "review of",
)


def _looks_like_non_product_page(url: str, title: str) -> bool:
    haystack = f"{url} {title}".lower()
    return any(signal in haystack for signal in NON_PRODUCT_SIGNALS)


class LiveSearchAgent(BaseAgent):
    """Discovers real product candidates via Serper search and (best-effort) page extraction."""

    name = "live_search"

    def __init__(self, client=None):
        super().__init__(client)
        self.suppliers = load_suppliers()
        self.supplier_cross_check = SupplierCrossCheckAgent(self.client)
        self.known_brands = get_all_known_brands()

    def _matching_suppliers(self, category: str, subcategory: str) -> List[Dict[str, Any]]:
        matches = [
            s
            for s in self.suppliers
            if category in s.get("specialties", []) or subcategory in s.get("specialties", [])
        ]
        return matches[:MAX_SUPPLIERS]

    def _match_supplier_for_url(self, url: str) -> Optional[Dict[str, Any]]:
        domain = urlparse(url).netloc.replace("www.", "")
        for s in self.suppliers:
            if urlparse(s["website"]).netloc.replace("www.", "") == domain:
                return s
        return None

    def _to_supplier_model(self, supplier_dict: Optional[Dict[str, Any]]) -> Optional[Supplier]:
        if not supplier_dict:
            return None
        return self.supplier_cross_check._dict_to_supplier(supplier_dict)

    def _guess_brand(self, title: str, fallback: str, supplier_dict: Optional[Dict[str, Any]]) -> str:
        title_lower = title.lower()
        # Prefer a known curated manufacturer brand over the retailer/source name —
        # e.g. "SARO Minibar MB 30 U" sold via "Gastrodax" should score as SARO, not Gastrodax.
        for brand in self.known_brands:
            if brand.lower() in title_lower:
                return brand
        if supplier_dict:
            for brand in supplier_dict.get("brands_carried", []):
                if brand.lower() in title_lower:
                    return brand
        if fallback:
            return fallback
        first_word = title.split()[0] if title.split() else "Unknown"
        return first_word

    def _product_from_shopping(
        self, hit: ShoppingResult, category: str, subcategory: str
    ) -> Optional[Product]:
        if not hit.title or not hit.link:
            return None
        supplier_dict = self._match_supplier_for_url(hit.link)
        return Product(
            id=hashlib.sha256(hit.link.encode()).hexdigest()[:16],
            name=hit.title,
            brand=self._guess_brand(hit.title, hit.source, supplier_dict),
            category=category,
            subcategory=subcategory,
            list_price_eur=hit.price_eur,
            source_url=hit.link,
            supplier=self._to_supplier_model(supplier_dict),
        )

    def _product_from_organic(
        self, result: OrganicResult, category: str, subcategory: str
    ) -> Optional[Product]:
        if _looks_like_non_product_page(result.link, result.title):
            return None

        try:
            page = self.client.get(result.link)
        except Exception:
            return None
        if page.status_code != 200:
            return None

        extracted = extract_manufacturer_specs(page)
        name = extracted.get("name") or result.title
        if not name or _looks_like_non_product_page(result.link, name):
            return None

        supplier_dict = self._match_supplier_for_url(result.link)
        prices = [p for p in extracted.get("price_candidates", []) if p >= MIN_PLAUSIBLE_PRICE_EUR]
        supplier_name = supplier_dict["name"] if supplier_dict else ""

        return Product(
            id=hashlib.sha256(result.link.encode()).hexdigest()[:16],
            name=name,
            brand=self._guess_brand(name, supplier_name, supplier_dict),
            category=category,
            subcategory=subcategory,
            specs=extracted.get("tables", [{}])[0] if extracted.get("tables") else {},
            list_price_eur=min(prices) if prices else None,
            source_url=result.link,
            supplier=self._to_supplier_model(supplier_dict),
        )

    def find_products(
        self, query: str, category: str, subcategory: Optional[str] = None
    ) -> List[Product]:
        subcategory = subcategory or category
        base_query = f"{query} {subcategory}".strip()
        suppliers = self._matching_suppliers(category, subcategory)

        products: Dict[str, Product] = {}

        try:
            shopping_hits = search_shopping(f"{base_query} hotel", num=SHOPPING_RESULTS)
        except Exception:
            shopping_hits = []
        for hit in shopping_hits:
            product = self._product_from_shopping(hit, category, subcategory)
            if product:
                products[product.source_url] = product

        organic_results: List[OrganicResult] = []
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {
                pool.submit(
                    search_organic, f"site:{urlparse(s['website']).netloc} {base_query}", ORGANIC_RESULTS_PER_SUPPLIER
                ): s
                for s in suppliers
            }
            for fut in as_completed(futures):
                try:
                    organic_results.extend(fut.result())
                except Exception:
                    continue

        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [
                pool.submit(self._product_from_organic, r, category, subcategory)
                for r in organic_results
                if r.link not in products
            ]
            for fut in as_completed(futures):
                product = fut.result()
                if product is not None and product.source_url not in products:
                    products[product.source_url] = product

        return list(products.values())

    def run(self, request: ResearchRequest) -> List[Product]:
        query = request.query or request.design_brief or request.category
        return self.find_products(query, request.category)
