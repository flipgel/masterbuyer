"""One-click inquiry email links ("mailto:") for a product result."""
from urllib.parse import quote, urlparse

from core.models import Product
from ui.rfq import generate_rfq_draft


def build_mailto_link(product: Product, hotel_name: str) -> str:
    """Build a mailto: link prefilled with an RFQ-style inquiry for this product.

    Recipient is a fast `info@<domain>` guess from the product's source URL, not a
    live page fetch — scraping every result's page just to grep for a contact email
    would mean one HTTP request per row on every render. The guess is editable by the
    user in their mail client before sending anyway.
    """
    domain = urlparse(product.source_url).netloc.replace("www.", "") if product.source_url else ""
    to_email = f"info@{domain}" if domain else ""

    draft = generate_rfq_draft(product, hotel_name=hotel_name)
    subject, _, body = draft.partition("\n\n")
    subject = subject.removeprefix("Subject: ")
    return f"mailto:{to_email}?subject={quote(subject)}&body={quote(body)}"
