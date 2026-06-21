"""AV specialist."""
from agents.category.base import CategoryAgent


class AVAgent(CategoryAgent):
    """Specialist for speakers and televisions."""

    name = "av"
    category_key = "av"
