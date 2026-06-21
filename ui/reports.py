"""CSV and PDF report generators."""
import csv
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from core.models import Product, ResearchResult


def generate_csv(result: ResearchResult) -> str:
    """Generate CSV content from a research result."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Rank", "Brand", "Name", "Category", "Subcategory", "Price EUR",
        "Quality", "Value", "Rarity", "Exclusivity", "TCO", "Compliance",
        "Overall", "TCO 10yr EUR", "Supplier", "Hotel Usage", "Warranty Years"
    ])
    for idx, p in enumerate(result.products, 1):
        writer.writerow([
            idx,
            p.brand,
            p.name,
            p.category,
            p.subcategory,
            p.effective_price,
            round(p.quality_score, 1),
            round(p.value_score, 1),
            round(p.rarity_score, 1),
            round(p.exclusivity_score, 1),
            round(p.tco_score, 1),
            round(p.compliance_score, 1),
            round(p.overall_score, 1),
            p.tco_10yr_eur,
            p.supplier.name if p.supplier else "",
            ", ".join(p.hotel_usage),
            p.warranty_years,
        ])
    return output.getvalue()


def generate_pdf(result: ResearchResult) -> bytes:
    """Generate a PDF spec report from a research result."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title = f"Procurement Report: {result.request.category.title()}"
    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph(f"Generated: {result.generated_at:%Y-%m-%d %H:%M}", styles["Normal"]))
    story.append(Spacer(1, 12))

    data = [["Rank", "Brand", "Product", "Price", "Overall", "Quality", "Exclusivity"]]
    for idx, p in enumerate(result.products[:10], 1):
        data.append([
            str(idx),
            p.brand,
            p.name,
            p.display_price,
            f"{p.overall_score:.0f}",
            f"{p.quality_score:.0f}",
            f"{p.exclusivity_score:.0f}",
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A1A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7F7")]),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    if result.hotel_benchmarks:
        story.append(Paragraph("Hotel Benchmarks", styles["Heading2"]))
        for b in result.hotel_benchmarks[:5]:
            story.append(Paragraph(f"• <b>{b.hotel_name}</b> — {b.brand} ({b.tier})", styles["Normal"]))
        story.append(Spacer(1, 12))

    if result.negotiation_briefs:
        story.append(Paragraph("Negotiation Briefs", styles["Heading2"]))
        for brief in result.negotiation_briefs[:3]:
            story.append(Paragraph(f"<b>{brief.supplier_name}</b> — {brief.product_name}", styles["Heading3"]))
            story.append(Paragraph(f"Market position: {brief.market_position}", styles["Normal"]))
            if brief.target_price_eur:
                story.append(Paragraph(f"Target price: €{brief.target_price_eur:,.2f}", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
