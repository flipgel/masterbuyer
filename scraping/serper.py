"""Client for the Serper.dev Google Search API (organic + shopping results).

Plain HTTP scraping of Google/Bing/DuckDuckGo is bot-walled for non-browser
clients (confirmed: both returned CAPTCHA/anomaly challenges in testing). Serper.dev
proxies real Google results over a simple JSON API, including Google Shopping
results which directly carry name/price/link/source — exactly what's needed for
procurement search without having to scrape individual (often bot-walled) B2B sites.
"""
import re
from dataclasses import dataclass
from typing import List, Optional

import requests

from core.cache import cache
from core.config import CACHE_TTL_SHORT_SECONDS, SERPER_API_KEY

SERPER_BASE_URL = "https://google.serper.dev"


class SerperConfigError(RuntimeError):
    """Raised when SERPER_API_KEY is not configured."""


@dataclass
class OrganicResult:
    title: str
    link: str
    snippet: str = ""


@dataclass
class ShoppingResult:
    title: str
    link: str
    source: str = ""
    price_text: Optional[str] = None
    price_eur: Optional[float] = None
    image_url: Optional[str] = None


def _require_api_key() -> str:
    if not SERPER_API_KEY:
        raise SerperConfigError(
            "SERPER_API_KEY is not set. Get a free key at https://serper.dev and "
            "add it to a .env file (see .env.example) or export it as an environment variable."
        )
    return SERPER_API_KEY


def _parse_price(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    match = re.search(r"[\d.,]+", text)
    if not match:
        return None
    raw = match.group(0).replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return None


# Europe / EUR-denominated results by default — this tool is Europe-focused and the
# UI displays prices in EUR. `gl=de` consistently returned EU hospitality suppliers
# with real EUR pricing in testing (vs. `gl=us` defaulting to USD/US consumer retailers).
DEFAULT_GL = "de"
DEFAULT_HL = "en"


def _post(path: str, payload: dict, ttl_seconds: int = CACHE_TTL_SHORT_SECONDS) -> dict:
    payload = {"gl": DEFAULT_GL, "hl": DEFAULT_HL, **payload}
    cache_key = f"{path}:{sorted(payload.items())}"
    cached = cache.get("serper", cache_key)
    if cached is not None:
        return cached

    api_key = _require_api_key()
    response = requests.post(
        f"{SERPER_BASE_URL}/{path}",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    cache.set("serper", cache_key, data, ttl_seconds=ttl_seconds)
    return data


def search_organic(query: str, num: int = 10) -> List[OrganicResult]:
    data = _post("search", {"q": query, "num": num})
    return [
        OrganicResult(
            title=item.get("title", ""),
            link=item.get("link", ""),
            snippet=item.get("snippet", ""),
        )
        for item in data.get("organic", [])
        if item.get("link")
    ]


def search_shopping(query: str, num: int = 10) -> List[ShoppingResult]:
    data = _post("shopping", {"q": query, "num": num})
    results = []
    for item in data.get("shopping", []):
        if not item.get("link"):
            continue
        price_text = item.get("price")
        results.append(
            ShoppingResult(
                title=item.get("title", ""),
                link=item["link"],
                source=item.get("source", ""),
                price_text=price_text,
                price_eur=_parse_price(price_text),
                image_url=item.get("imageUrl"),
            )
        )
    return results
