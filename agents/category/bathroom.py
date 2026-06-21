"""Bathroom accessories & amenities specialist."""
from agents.category.base import CategoryAgent


class BathroomAgent(CategoryAgent):
    """Specialist for dispensers, towels, and toiletries."""

    name = "bathroom"
    category_key = "bathroom"
