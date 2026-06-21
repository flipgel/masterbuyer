"""Tests for scraping utilities."""
import pytest

from scraping.extractors import extract_review_snippets
from scraping.parsers import extract_price_candidates, extract_text


def test_extract_price_candidates():
    text = "The Dyson Supersonic costs €389.00 and the ghd is €169."
    prices = extract_price_candidates(text)
    assert 389.0 in prices
    assert 169.0 in prices


def test_extract_text_basic():
    html = "<html><body><p>This is a test paragraph.</p></body></html>"
    text = extract_text(html)
    assert "test paragraph" in text


def test_extract_review_snippets():
    text = "This product is excellent and durable. However, it is a bit noisy. Great service."
    snippets = extract_review_snippets(text)
    assert len(snippets) > 0
    sentiments = {s["sentiment"] for s in snippets}
    assert "positive" in sentiments
