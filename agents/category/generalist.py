"""Generalist agent for categories with lighter coverage."""
from agents.category.base import CategoryAgent


class GeneralistAgent(CategoryAgent):
    """Lighter coverage for faucets, showers, telephones, Wi-Fi, projectors, furniture."""

    name = "general"
    category_key = "general"
