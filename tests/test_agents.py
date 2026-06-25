"""Tests for agent layer."""
import pytest

from agents.analysis.compliance import ComplianceAgent
from agents.analysis.exclusivity import ExclusivityAgent
from agents.analysis.quality_price import QualityPriceAgent
from agents.analysis.supplier_cross_check import SupplierCrossCheckAgent
from agents.analysis.tco import TCOAgent
from agents.orchestrator import OrchestratorAgent
from core.models import Product, ResearchRequest, ReviewSignals


def _fake_products(category, subcategory):
    return [
        Product(id="1", name="Test Hairdryer", brand="Dyson", category=category, subcategory=subcategory, list_price_eur=300),
        Product(id="2", name="Test Hairdryer 2", brand="ghd", category=category, subcategory=subcategory, list_price_eur=150),
    ]


def test_orchestrator_hairdryer(mocker):
    mocker.patch(
        "agents.research.live_search.LiveSearchAgent.find_products",
        side_effect=lambda query, category, subcategory=None: _fake_products(category, subcategory),
    )
    agent = OrchestratorAgent()
    result = agent.run(ResearchRequest(category="hairdryer", quantity=80))
    assert len(result.products) > 0
    assert all(p.overall_score > 0 for p in result.products)
    assert result.top_product is not None


def test_orchestrator_bathroom(mocker):
    mocker.patch(
        "agents.research.live_search.LiveSearchAgent.find_products",
        side_effect=lambda query, category, subcategory=None: _fake_products(category, subcategory),
    )
    agent = OrchestratorAgent()
    result = agent.run(ResearchRequest(category="towel", quantity=200))
    assert len(result.products) > 0


def test_exclusivity_agent():
    agent = ExclusivityAgent()
    score = agent.score_brand("Bang & Olufsen", ["Aman"])
    assert 0 <= score["rarity_score"] <= 100
    assert 0 <= score["exclusivity_score"] <= 100


def test_quality_agent():
    agent = QualityPriceAgent()
    p = Product(id="1", name="Test", brand="Dyson", category="appliances", subcategory="hairdryer")
    p.specs = {"power_w": 1600, "noise_db": 77}
    p.warranty_years = 2
    result = agent.score_product(p, brand_tier="ultra_luxury")
    assert 0 <= result["quality_score"] <= 100


def test_tco_agent():
    agent = TCOAgent()
    p = Product(id="1", name="Test", brand="Dometic", category="appliances", subcategory="minibar")
    p.list_price_eur = 300
    result = agent.estimate(p)
    assert result["tco_10yr_eur"] is not None
    assert result["tco_10yr_eur"] > 300


def test_compliance_agent():
    agent = ComplianceAgent()
    p = Product(id="1", name="Test", brand="Samsung", category="av", subcategory="television")
    p.certifications = ["CE", "Energy Label"]
    p.warranty_years = 3
    result = agent.check_product(p)
    assert result["compliance_score"] > 80


def test_supplier_agent():
    agent = SupplierCrossCheckAgent()
    suppliers = agent.find_suppliers_for_brand("Dyson")
    assert len(suppliers) > 0
