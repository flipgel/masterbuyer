"""Tests for scoring engine."""
import pytest

from core.models import Product
from core.scoring import ScoreWeights, clamp, compute_overall_score, compute_tco_score, compute_value_score, rank_products


def test_clamp():
    assert clamp(105) == 100.0
    assert clamp(-5) == 0.0
    assert clamp(50) == 50.0


def test_compute_value_score_with_price():
    p = Product(id="1", name="Test", brand="Test", category="av", subcategory="speaker", quality_score=80)
    p.list_price_eur = 100
    assert compute_value_score(p, 100) == pytest.approx(80, rel=1e-2)


def test_compute_value_score_no_price():
    p = Product(id="1", name="Test", brand="Test", category="av", subcategory="speaker", quality_score=80)
    assert compute_value_score(p, None) == pytest.approx(60, rel=1e-2)


def test_compute_tco_score():
    p = Product(id="1", name="Test", brand="Test", category="appliances", subcategory="minibar")
    p.list_price_eur = 1000
    p.tco_10yr_eur = 1000
    assert compute_tco_score(p) > 50


def test_rank_products():
    p1 = Product(id="1", name="A", brand="A", category="av", subcategory="speaker", quality_score=90)
    p1.list_price_eur = 200
    p2 = Product(id="2", name="B", brand="B", category="av", subcategory="speaker", quality_score=60)
    p2.list_price_eur = 100
    ranked = rank_products([p1, p2])
    assert len(ranked) == 2
    assert all(p.overall_score > 0 for p in ranked)
    assert ranked == sorted(ranked, key=lambda p: p.overall_score, reverse=True)


def test_score_weights_validation():
    w = ScoreWeights(rarity=0.2, quality=0.3, value=0.2, tco=0.1, exclusivity=0.1, compliance=0.1)
    w.validate()

    with pytest.raises(ValueError):
        ScoreWeights(rarity=0.5, quality=0.5).validate()
