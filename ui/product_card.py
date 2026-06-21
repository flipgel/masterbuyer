"""Detailed product card renderer."""
import streamlit as st

from core.models import Product
from core.scoring import score_to_grade


def render_product_card(product: Product, rank: int = 1) -> None:
    """Render a detailed product card in Streamlit."""
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            if product.source_url:
                st.subheader(f"#{rank} [{product.brand} {product.name}]({product.source_url})")
            else:
                st.subheader(f"#{rank} {product.brand} {product.name}")
            st.caption(f"{product.subcategory.title()} · {product.display_price}")
        with col2:
            st.metric("Overall Score", f"{product.overall_score:.0f}", score_to_grade(product.overall_score))
            if product.source_url:
                st.link_button("Open official page ↗", product.source_url, use_container_width=True)

        score_cols = st.columns(6)
        score_cols[0].metric("Quality", f"{product.quality_score:.0f}")
        score_cols[1].metric("Value", f"{product.value_score:.0f}")
        score_cols[2].metric("Rarity", f"{product.rarity_score:.0f}")
        score_cols[3].metric("Exclusivity", f"{product.exclusivity_score:.0f}")
        score_cols[4].metric("TCO", f"{product.tco_score:.0f}")
        score_cols[5].metric("Compliance", f"{product.compliance_score:.0f}")

        st.markdown("**Specifications**")
        if product.specs:
            spec_text = " · ".join([f"**{k}:** {v}" for k, v in product.specs.items()])
            st.markdown(spec_text)
        else:
            st.caption("No specs available.")

        if product.tco_10yr_eur:
            st.markdown(f"**10-year TCO estimate:** €{product.tco_10yr_eur:,.2f}")

        if product.pros:
            st.markdown("**Pros**")
            for pro in product.pros:
                st.markdown(f"- {pro}")
        if product.cons:
            st.markdown("**Cons**")
            for con in product.cons:
                st.markdown(f"- {con}")

        if product.hotel_usage:
            st.markdown(f"**Used by:** {', '.join(product.hotel_usage)}")

        if product.supplier:
            s = product.supplier
            st.markdown(
                f"**Supplier:** [{s.name}]({s.website}) · {s.country} · "
                f"Service: {', '.join(s.service_countries) or 'N/A'}"
            )

        if product.compliance_flags:
            st.warning("Compliance flags: " + "; ".join(product.compliance_flags))
