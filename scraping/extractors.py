"""Site-specific extractors for common hospitality data sources."""
import re
from typing import Any, Dict, List, Optional

from scraping.client import FetchResult
from scraping.parsers import extract_og_image, extract_price_candidates, extract_text, parse_html


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_dyson_product(result: FetchResult) -> Dict[str, Any]:
    soup = parse_html(result.text)
    name = soup.find("h1")
    price_tag = soup.find("span", class_=re.compile("price", re.I))
    price = None
    if price_tag:
        candidates = extract_price_candidates(price_tag.get_text())
        if candidates:
            price = candidates[0]
    return {
        "name": _clean(name.get_text()) if name else None,
        "price_eur": price,
        "source_url": result.url,
    }


def extract_amazon_product(result: FetchResult) -> Dict[str, Any]:
    """Basic Amazon product extraction (for reference; scraping Amazon is fragile)."""
    soup = parse_html(result.text)
    name = soup.find("span", id="productTitle")
    price_whole = soup.find("span", class_="a-price-whole")
    price_fraction = soup.find("span", class_="a-price-fraction")
    price = None
    if price_whole and price_fraction:
        try:
            price = float(f"{price_whole.get_text(strip=True)}{price_fraction.get_text(strip=True)}")
        except ValueError:
            pass
    rating = soup.find("span", class_="a-icon-alt")
    review_count = soup.find("span", id="acrCustomerReviewText")
    return {
        "name": _clean(name.get_text()) if name else None,
        "price_eur": price,
        "rating_text": _clean(rating.get_text()) if rating else None,
        "review_count_text": _clean(review_count.get_text()) if review_count else None,
        "source_url": result.url,
    }


def extract_manufacturer_specs(result: FetchResult) -> Dict[str, Any]:
    """Generic extractor for manufacturer spec pages."""
    text = extract_text(result.text)
    soup = parse_html(result.text)
    name = soup.find("h1")
    data = {
        "name": _clean(name.get_text()) if name else None,
        "description": text[:2000] if text else None,
        "price_candidates": extract_price_candidates(text)[:5],
        "tables": [],
        "source_url": result.url,
        "image_url": extract_og_image(result.text),
    }
    # Extract specification tables
    for table in soup.find_all("table"):
        rows = {}
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if len(cells) >= 2:
                rows[_clean(cells[0])] = _clean(cells[1])
        if rows:
            data["tables"].append(rows)
    return data


def extract_review_snippets(text: str, max_snippets: int = 10) -> List[Dict[str, str]]:
    """Extract review-like sentences from text for sentiment analysis."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    positive_phrases = re.compile(
        r"\b(excellent|amazing|love|perfect|great|fantastic|quiet|reliable|durable|high quality|premium|worth)\b",
        re.IGNORECASE,
    )
    negative_phrases = re.compile(
        r"\b(terrible|awful|broke|noisy|cheap|disappointed|poor quality|issue|problem|returned)\b",
        re.IGNORECASE,
    )
    snippets = []
    for sentence in sentences:
        if len(sentence) < 20:
            continue
        sentiment = "neutral"
        if positive_phrases.search(sentence) and not negative_phrases.search(sentence):
            sentiment = "positive"
        elif negative_phrases.search(sentence) and not positive_phrases.search(sentence):
            sentiment = "negative"
        if sentiment != "neutral" or any(kw in sentence.lower() for kw in ["durability", "noise", "service", "warranty"]):
            snippets.append({"text": _clean(sentence), "sentiment": sentiment})
        if len(snippets) >= max_snippets:
            break
    return snippets
