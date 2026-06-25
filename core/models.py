"""Dataclasses that power the procurement research tool."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Supplier:
    """A supplier or distributor of hospitality products."""
    name: str
    country: str
    website: str
    is_authorized: bool = False
    service_countries: List[str] = field(default_factory=list)
    moq: Optional[int] = None
    certifications: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class HotelBenchmark:
    """A data point about what a leading hotel uses."""
    hotel_name: str
    hotel_group: Optional[str]
    location: str
    tier: str  # budget/midscale/upscale/luxury
    category: str
    brand: str
    product_line: Optional[str]
    source_url: Optional[str]
    notes: str = ""


@dataclass
class ReviewSignals:
    """Aggregated review/forum signals about a brand or product."""
    source_count: int = 0
    avg_sentiment: float = 0.0  # -1 to 1
    durability_mentions: int = 0
    noise_mentions: int = 0
    service_mentions: int = 0
    positive_phrases: List[str] = field(default_factory=list)
    negative_phrases: List[str] = field(default_factory=list)


@dataclass
class Product:
    """A researched product candidate."""
    id: str
    name: str
    brand: str
    category: str
    subcategory: str
    specs: Dict[str, Any] = field(default_factory=dict)
    list_price_eur: Optional[float] = None
    estimated_price_eur: Optional[float] = None
    supplier: Optional[Supplier] = None
    source_url: Optional[str] = None
    availability_weeks: Optional[int] = None
    warranty_years: Optional[float] = None
    certifications: List[str] = field(default_factory=list)
    hotel_usage: List[str] = field(default_factory=list)
    review_signals: ReviewSignals = field(default_factory=ReviewSignals)

    # Scores 0-100
    rarity_score: float = 0.0
    quality_score: float = 0.0
    value_score: float = 0.0
    tco_score: float = 0.0
    exclusivity_score: float = 0.0
    compliance_score: float = 0.0
    overall_score: float = 0.0

    # Analysis outputs
    tco_10yr_eur: Optional[float] = None
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    compliance_flags: List[str] = field(default_factory=list)
    notes: str = ""

    @property
    def effective_price(self) -> Optional[float]:
        return self.list_price_eur or self.estimated_price_eur

    @property
    def display_price(self) -> str:
        price = self.effective_price
        if price is None:
            return "Price on request"
        return f"€{price:,.2f}"


@dataclass
class NegotiationBrief:
    """One-page brief for negotiating with a supplier."""
    supplier_name: str
    product_name: str
    market_position: str
    alternatives: List[str] = field(default_factory=list)
    leverage_points: List[str] = field(default_factory=list)
    target_price_eur: Optional[float] = None
    suggested_terms: List[str] = field(default_factory=list)


@dataclass
class ResearchRequest:
    """A user request for procurement research."""
    category: str
    quantity: int = 1
    budget_per_unit_eur: Optional[float] = None
    query: str = ""
    design_brief: str = ""
    must_have: List[str] = field(default_factory=list)
    nice_to_have: List[str] = field(default_factory=list)
    sustainability_priority: bool = False
    local_service_required: bool = True


@dataclass
class ResearchResult:
    """The full output of a research run."""
    request: ResearchRequest
    products: List[Product] = field(default_factory=list)
    hotel_benchmarks: List[HotelBenchmark] = field(default_factory=list)
    negotiation_briefs: List[NegotiationBrief] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def top_product(self) -> Optional[Product]:
        if not self.products:
            return None
        return max(self.products, key=lambda p: p.overall_score)


@dataclass
class HotelProfile:
    """Persistent hotel project profile."""
    name: str = ""
    location_country: str = ""
    city: str = ""
    star_rating: str = "5-star luxury"
    room_count: int = 0
    design_dna: str = ""
    sustainability_priority: bool = False
    local_service_required: bool = True
