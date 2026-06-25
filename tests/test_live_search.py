"""Tests for live product search (Serper-backed), fully mocked — no network access."""
from datetime import datetime

import pytest

from agents.research.live_search import LiveSearchAgent
from scraping.client import FetchResult
from scraping.serper import OrganicResult, ShoppingResult


def _fetch_result(url, text, status_code=200):
    return FetchResult(
        url=url,
        status_code=status_code,
        headers={},
        text=text,
        elapsed_ms=1,
        from_cache=False,
        fetched_at=datetime.now(),
    )


def test_find_products_uses_shopping_results(mocker):
    mocker.patch(
        "agents.research.live_search.search_shopping",
        return_value=[
            ShoppingResult(
                title="Dometic MiniCool Hotel Fridge",
                link="https://www.dometic.com/en-us/product/minicool",
                source="Dometic",
                price_text="EUR 312.00",
                price_eur=312.0,
            )
        ],
    )
    mocker.patch("agents.research.live_search.search_organic", return_value=[])

    agent = LiveSearchAgent()
    products = agent.find_products("minibar fridge", "appliances", "minibar")

    assert len(products) == 1
    p = products[0]
    assert p.name == "Dometic MiniCool Hotel Fridge"
    assert p.list_price_eur == 312.0
    assert p.source_url == "https://www.dometic.com/en-us/product/minicool"
    assert p.supplier is not None
    assert p.supplier.name == "Dometic Hospitality"


def test_find_products_enriches_from_organic_pages(mocker):
    mocker.patch("agents.research.live_search.search_shopping", return_value=[])
    mocker.patch(
        "agents.research.live_search.search_organic",
        return_value=[
            OrganicResult(
                title="Technomax Hotel Safe",
                link="https://www.technomax.it/products/hotel-safe",
                snippet="Hotel safes",
            )
        ],
    )
    page_html = "<html><body><h1>Technomax Hotel Safe</h1><p>Price: EUR 245.00</p></body></html>"
    agent = LiveSearchAgent()
    mocker.patch.object(
        agent.client, "get", return_value=_fetch_result("https://www.technomax.it/products/hotel-safe", page_html)
    )

    products = agent.find_products("hotel safe", "appliances", "safe")

    assert len(products) == 1
    p = products[0]
    assert "Technomax" in p.name
    assert p.list_price_eur == 245.0


def test_find_products_skips_unfetchable_organic_pages(mocker):
    mocker.patch("agents.research.live_search.search_shopping", return_value=[])
    mocker.patch(
        "agents.research.live_search.search_organic",
        return_value=[
            OrganicResult(title="Blocked Page", link="https://www.nisbets.co.uk/blocked", snippet="")
        ],
    )
    agent = LiveSearchAgent()
    mocker.patch.object(
        agent.client, "get", return_value=_fetch_result("https://www.nisbets.co.uk/blocked", "", status_code=403)
    )

    products = agent.find_products("combi oven", "back_of_house", "cooking")

    assert products == []


def test_find_products_dedupes_shopping_and_organic_by_url(mocker):
    shared_url = "https://www.dometic.com/en-us/product/minicool"
    mocker.patch(
        "agents.research.live_search.search_shopping",
        return_value=[ShoppingResult(title="Dometic Fridge", link=shared_url, price_eur=300.0)],
    )
    mocker.patch(
        "agents.research.live_search.search_organic",
        return_value=[OrganicResult(title="Dometic Fridge", link=shared_url, snippet="")],
    )
    agent = LiveSearchAgent()
    products = agent.find_products("minibar fridge", "appliances", "minibar")

    assert len(products) == 1
