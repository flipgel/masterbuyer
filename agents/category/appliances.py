"""Guest-room appliances specialist."""
from agents.category.base import CategoryAgent


class AppliancesAgent(CategoryAgent):
    """Specialist for fridges, minibars, safes, kettles, irons, hairdryers."""

    name = "appliances"
    category_key = "appliances"
