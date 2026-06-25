"""Tests for free-text query -> category inference."""
from core.query_intent import infer_category


def test_infer_category_exact_subcategory():
    assert infer_category("kettle") == "kettle"


def test_infer_category_within_sentence():
    assert infer_category("I need a luxury minibar fridge for guest rooms") == "minibar"


def test_infer_category_case_insensitive():
    assert infer_category("Brass Bathroom FAUCET") == "faucet"


def test_infer_category_unknown_falls_back_to_general():
    assert infer_category("something totally unrelated to hotels") == "general"
