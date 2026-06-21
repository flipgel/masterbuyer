"""Main dashboard UI with filters and ranked product table."""
import pandas as pd
import streamlit as st

from core.models import Product, ResearchResult
from core.scoring import score_to_grade
from ui.product_card import render_product_card


def render_dashboard(result: ResearchResult) -> None:
    """Render the interactive dashboard tab."""
    st.header("Ranked Product Dashboard")

    if not result.products:
        st.info("No products found for this request.")
        return

    products = result.products

    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        brand_filter = st.multiselect(
            "Brand",
            options=sorted({p.brand for p in products}),
            default=[],
        )
    with col2:
        min_score = st.slider("Min overall score", 0, 100, 0)
    with col3:
        max_price = st.number_input(
            "Max price (EUR)",
            min_value=0.0,
            value=max([p.effective_price or 0 for p in products]) * 1.2 or 1000.0,
        )
    with col4:
        sort_by = st.selectbox(
            "Sort by",
            ["overall_score", "quality_score", "value_score", "exclusivity_score", "tco_score"],
        )

    filtered = [p for p in products if p.overall_score >= min_score]
    if brand_filter:
        filtered = [p for p in filtered if p.brand in brand_filter]
    filtered = [p for p in filtered if (p.effective_price or 0) <= max_price or p.effective_price is None]
    filtered = sorted(filtered, key=lambda p: getattr(p, sort_by), reverse=True)

    st.write(f"Showing {len(filtered)} of {len(products)} products")

    # Data table
    df = pd.DataFrame([
        {
            "Rank": i + 1,
            "Brand": p.brand,
            "Product": p.name,
            "Subcategory": p.subcategory,
            "Price": p.display_price,
            "Overall": f"{p.overall_score:.0f} ({score_to_grade(p.overall_score)})",
            "Quality": f"{p.quality_score:.0f}",
            "Value": f"{p.value_score:.0f}",
            "Rarity": f"{p.rarity_score:.0f}",
            "Exclusivity": f"{p.exclusivity_score:.0f}",
            "TCO": f"{p.tco_score:.0f}",
            "Compliance": f"{p.compliance_score:.0f}",
        }
        for i, p in enumerate(filtered)
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Top product cards
    st.subheader("Top Candidates")
    for i, p in enumerate(filtered[:5], 1):
        render_product_card(p, rank=i)
