"""Hotel benchmark agent: finds what leading hotels use for a category."""
from typing import Dict, List

from agents.base import BaseAgent
from core.data_loader import load_hotel_brands
from core.models import HotelBenchmark, ResearchRequest


class HotelBenchmarkAgent(BaseAgent):
    """Compare requested category against curated luxury hotel brand standards."""

    name = "hotel_benchmark"

    def __init__(self, client=None):
        super().__init__(client)
        self.hotels = load_hotel_brands()

    def find_benchmarks(self, category: str, subcategory: str | None = None) -> List[HotelBenchmark]:
        """Return hotels that specify brands for the requested category/subcategory."""
        results = []
        key = subcategory or category
        for hotel in self.hotels:
            amenity_brands = hotel.get("amenity_brands", {})
            matched_brands = amenity_brands.get(key, [])
            if not matched_brands:
                continue
            for brand in matched_brands:
                results.append(
                    HotelBenchmark(
                        hotel_name=hotel["name"],
                        hotel_group=hotel.get("group"),
                        location=hotel.get("regions", ["global"])[0],
                        tier=hotel.get("tier", "luxury"),
                        category=category,
                        brand=brand,
                        product_line=None,
                        source_url=None,
                        notes=hotel.get("notes", ""),
                    )
                )
        return results

    def brand_presence_in_luxury_hotels(self, brand: str) -> Dict[str, any]:
        """Count how often a brand appears in the benchmark dataset."""
        count = 0
        hotels_list = []
        for hotel in self.hotels:
            for cat, brands in hotel.get("amenity_brands", {}).items():
                if brand.lower() in [b.lower() for b in brands]:
                    count += 1
                    hotels_list.append((hotel["name"], cat))
        return {"count": count, "hotels": hotels_list}

    def run(self, request: ResearchRequest) -> List[HotelBenchmark]:
        return self.find_benchmarks(request.category)
