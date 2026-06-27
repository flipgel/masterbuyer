"""Load curated JSON datasets into Python objects."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import DATA_DIR


def _load_json(name: str) -> Dict[str, Any]:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_category_taxonomy() -> Dict[str, Any]:
    return _load_json("category_taxonomy.json")


def load_hotel_brands() -> List[Dict[str, Any]]:
    return _load_json("hotel_brands.json").get("hotels", [])


def load_suppliers() -> List[Dict[str, Any]]:
    return _load_json("supplier_index.json").get("suppliers", [])


def get_category_weights(category: str) -> Dict[str, float]:
    taxonomy = load_category_taxonomy()
    cats = taxonomy.get("categories", {})
    if category in cats:
        return cats[category].get("weights", {})
    return {}


def get_brand_rarity(brand: str) -> Dict[str, Any]:
    taxonomy = load_category_taxonomy()
    return taxonomy.get("brand_rarity", {}).get(brand, {})


def load_brand_catalog() -> Dict[str, Any]:
    """Map brand names to their official website and notes."""
    return _load_json("brand_catalog.json").get("brands", {})


def lookup_brand(query: str) -> Optional[Dict[str, Any]]:
    """Return catalog entry if the query starts with a known brand name, else None."""
    catalog = load_brand_catalog()
    q = query.lower().strip()
    # Sort longest-first so "Arc International" wins over "Arc" if both existed.
    for name in sorted(catalog, key=len, reverse=True):
        if q == name.lower() or q.startswith(name.lower() + " "):
            return {"name": name, **catalog[name]}
    return None


def get_all_known_brands() -> List[str]:
    """All curated brand names across every category's brand_tiers, longest first.

    Useful for spotting a known manufacturer brand inside a live search result's
    title (longest-first avoids e.g. matching "Le Labo" before "Le Labo Hospitality").
    """
    taxonomy = load_category_taxonomy()
    brands = set()
    for cat in taxonomy.get("categories", {}).values():
        for tier_brands in cat.get("brand_tiers", {}).values():
            brands.update(tier_brands)
    return sorted(brands, key=len, reverse=True)
