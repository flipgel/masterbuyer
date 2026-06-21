"""Back-of-house & F&B equipment specialist."""
from agents.category.base import CategoryAgent


class BackOfHouseAgent(CategoryAgent):
    """Specialist for kitchen, housekeeping, laundry, and F&B equipment."""

    name = "back_of_house"
    category_key = "back_of_house"
