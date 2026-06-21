"""RFQ email draft generator."""
from typing import List

from core.models import Product, ResearchResult


def generate_rfq_draft(
    product: Product,
    hotel_name: str = "Our Hotel Project",
    contact_name: str = "Procurement Team",
    quantity: int = 1,
    target_country: str = "EU",
) -> str:
    """Generate an RFQ email draft for a product."""
    subject = f"RFQ: {product.brand} {product.name} — {quantity} units"
    body = f"""Dear {product.supplier.name if product.supplier else product.brand} Team,

I am writing on behalf of {hotel_name}, a luxury 5-star hotel project in {target_country}, to request a quotation for the following item:

Product: {product.brand} {product.name}
Category: {product.subcategory.title()}
Quantity required: {quantity} units
Target delivery: {target_country}

Please provide:
1. Unit price (EUR, ex-works and DDP {target_country} if available)
2. Volume discount structure
3. Lead time from order confirmation
4. Warranty terms and after-sales service coverage
5. Samples availability and cost
6. Payment terms
7. Energy efficiency class and CE certification confirmation

We are also evaluating alternative suppliers, so we would appreciate your most competitive commercial offer.

Thank you,
{contact_name}
{hotel_name}
"""
    return f"Subject: {subject}\n\n{body}"


def generate_all_rfq_drafts(result: ResearchResult, hotel_name: str = "Our Hotel Project") -> str:
    """Generate RFQ drafts for the top 3 products."""
    drafts = []
    for product in result.products[:3]:
        drafts.append(generate_rfq_draft(product, hotel_name=hotel_name, quantity=result.request.quantity))
    return "\n\n" + "=" * 60 + "\n\n".join(drafts)
