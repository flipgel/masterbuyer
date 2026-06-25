"""Common HTML parsing helpers built on BeautifulSoup and Trafilatura."""
import re
import threading
from typing import List, Optional

from bs4 import BeautifulSoup
from trafilatura import extract

# lxml/libxml2 (used by both BeautifulSoup's "lxml" parser and trafilatura internally) is
# not safe to call concurrently from multiple threads — it reliably crashes the process
# (heap corruption) when LiveSearchAgent fetches/parses several pages in parallel via
# ThreadPoolExecutor. Network fetches stay parallel; only the brief parsing step is serialized.
_PARSE_LOCK = threading.Lock()


def parse_html(html: str) -> BeautifulSoup:
    with _PARSE_LOCK:
        return BeautifulSoup(html, "lxml")


def extract_title(html: str) -> Optional[str]:
    soup = parse_html(html)
    title = soup.find("title")
    return title.get_text(strip=True) if title else None


def extract_text(html: str, include_comments: bool = False) -> str:
    """Extract readable text from HTML using Trafilatura."""
    with _PARSE_LOCK:
        return (
            extract(
                html,
                include_comments=include_comments,
                include_tables=True,
                deduplicate=True,
            )
            or ""
        )


def extract_meta_description(html: str) -> Optional[str]:
    soup = parse_html(html)
    meta = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    if meta:
        return meta.get("content", "").strip() or None
    return None


def extract_og_image(html: str) -> Optional[str]:
    soup = parse_html(html)
    meta = soup.find("meta", attrs={"property": "og:image"}) or soup.find(
        "meta", attrs={"name": "twitter:image"}
    )
    if meta:
        return meta.get("content", "").strip() or None
    return None


def extract_links(html: str, base_url: Optional[str] = None) -> List[str]:
    soup = parse_html(html)
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if base_url and href.startswith("/"):
            from urllib.parse import urljoin
            href = urljoin(base_url, href)
        links.append(href)
    return links


_NUMBER = r"[0-9]{1,6}(?:[.,][0-9]{2})?"
_CURRENCY = r"€|£|\$|EUR|GBP|USD|euro|euros"
# European sites commonly write the currency after the number (e.g. "289,65 €") as well
# as before it (e.g. "€289.65") — match both orders.
_PRICE_PATTERNS = [
    re.compile(rf"(?:{_CURRENCY})\s*({_NUMBER})", re.IGNORECASE),
    re.compile(rf"({_NUMBER})\s*(?:{_CURRENCY})", re.IGNORECASE),
]


def extract_price_candidates(text: str) -> List[float]:
    """Find likely price values in text (requires an adjacent currency marker).

    The currency marker is required, not optional — otherwise this matches any bare
    number in running prose (e.g. a blog post mentioning "10 tips" or a stray date),
    which produced bogus "prices" when scraping non-product pages.
    """
    if not text:
        return []
    candidates = []
    for pattern in _PRICE_PATTERNS:
        for match in pattern.findall(text):
            cleaned = match.replace(",", "").replace(".", ".")
            try:
                value = float(cleaned)
                if 1 <= value <= 100000:
                    candidates.append(value)
            except ValueError:
                continue
    return candidates


def extract_tables(html: str) -> List[dict]:
    """Return list of tables as list-of-lists plus caption."""
    soup = parse_html(html)
    tables = []
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        caption = table.find("caption")
        tables.append(
            {
                "caption": caption.get_text(strip=True) if caption else "",
                "rows": rows,
            }
        )
    return tables
