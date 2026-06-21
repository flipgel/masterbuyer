"""Common HTML parsing helpers built on BeautifulSoup and Trafilatura."""
import re
from typing import List, Optional

from bs4 import BeautifulSoup
from trafilatura import extract


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def extract_title(html: str) -> Optional[str]:
    soup = parse_html(html)
    title = soup.find("title")
    return title.get_text(strip=True) if title else None


def extract_text(html: str, include_comments: bool = False) -> str:
    """Extract readable text from HTML using Trafilatura."""
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


def extract_price_candidates(text: str) -> List[float]:
    """Find likely price values in text (€, EUR, euro)."""
    if not text:
        return []
    pattern = re.compile(
        r"(?:€|EUR|euro|euros)?\s*([0-9]{1,6}(?:[.,][0-9]{2})?)",
        re.IGNORECASE,
    )
    candidates = []
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
