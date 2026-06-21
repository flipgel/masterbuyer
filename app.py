"""Hotel Procurement Research Tool — Streamlit entry point."""
import streamlit as st

from agents.orchestrator import OrchestratorAgent
from core.models import (
    HotelBenchmark,
    HotelProfile,
    NegotiationBrief,
    Product,
    ResearchRequest,
    ResearchResult,
)
from ui.dashboard import render_dashboard
from ui.product_card import render_product_card
from ui.reports import generate_csv, generate_pdf
from ui.rfq import generate_all_rfq_drafts


st.set_page_config(
    page_title="Hotel Procurement Research",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom luxury styling
st.markdown(
    """
    <style>
    :root {
        --hotel-navy: #0A192F;
        --hotel-gold: #C5A059;
        --hotel-cream: #FAF8F5;
        --hotel-charcoal: #1A1A1A;
    }
    .main {
        background-color: var(--hotel-cream);
    }
    h1, h2, h3 {
        color: var(--hotel-navy) !important;
    }
    .stButton>button {
        background-color: var(--hotel-navy);
        color: white;
        border-radius: 4px;
    }
    .stButton>button:hover {
        background-color: var(--hotel-gold);
        color: var(--hotel-navy);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session_state() -> None:
    defaults = {
        "hotel_profile": HotelProfile(),
        "last_result": None,
        "selected_product_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_data(ttl=3600)
def run_research(category: str, quantity: int, budget: float | None, design_brief: str, must_have: str) -> ResearchResult:
    """Run research and return a ResearchResult object (cached via pickle)."""
    request = ResearchRequest(
        category=category,
        quantity=quantity,
        budget_per_unit_eur=budget if budget > 0 else None,
        design_brief=design_brief,
        must_have=[x.strip() for x in must_have.split(",") if x.strip()],
    )
    orchestrator = OrchestratorAgent()
    return orchestrator.run(request)


def render_sidebar() -> None:
    with st.sidebar:
        st.title("🏨 Hotel Procurement")
        st.markdown("*Luxury 5-star research co-pilot*")

        st.header("Hotel Profile")
        profile = st.session_state.hotel_profile
        profile.name = st.text_input("Hotel project name", value=profile.name)
        profile.location_country = st.text_input("Country", value=profile.location_country or "Europe")
        profile.city = st.text_input("City", value=profile.city)
        profile.star_rating = st.selectbox(
            "Star rating / positioning",
            ["5-star luxury", "4-star upscale", "3-star midscale", "Boutique design"],
            index=0,
        )
        profile.room_count = st.number_input("Room count", min_value=0, value=profile.room_count, step=1)
        profile.design_dna = st.text_area(
            "Design DNA / guest experience",
            value=profile.design_dna,
            placeholder="e.g. Warm minimalism, sustainable materials, quiet technology...",
        )
        profile.sustainability_priority = st.checkbox("Sustainability is a priority", value=profile.sustainability_priority)
        profile.local_service_required = st.checkbox("Require local EU service network", value=profile.local_service_required)

        st.header("New Research Request")
        category = st.selectbox(
            "Category",
            [
                "hairdryer", "minibar", "safe", "kettle", "iron", "fridge",
                "speaker", "television",
                "dispenser", "towel", "toiletries",
                "cooking", "dishwashing", "laundry", "housekeeping", "small_equipment",
                "faucet", "shower", "telephone", "wifi", "projector", "furniture",
            ],
        )
        quantity = st.number_input("Quantity needed", min_value=1, value=80, step=1)
        budget = st.number_input("Budget per unit (EUR, 0 = no limit)", min_value=0.0, value=0.0, step=50.0)
        design_brief = st.text_area(
            "Design brief / notes",
            placeholder="e.g. Must match warm brass bathroom fittings, quiet for guest rooms...",
        )
        must_have = st.text_input("Must-haves (comma separated)", placeholder="e.g. CE mark, 5-year warranty")

        run_button = st.button("Run Research", type="primary", use_container_width=True)

        if run_button:
            with st.spinner("Running multi-agent research..."):
                result = run_research(category, quantity, budget, design_brief, must_have)
                st.session_state.last_result = result
                st.success(f"Found {len(result.products)} products")

        if st.session_state.last_result:
            st.divider()
            st.header("Export")
            result_obj = st.session_state.last_result

            csv_data = generate_csv(result_obj)
            st.download_button(
                "Download CSV",
                data=csv_data,
                file_name=f"procurement_{category}.csv",
                mime="text/csv",
                use_container_width=True,
            )

            pdf_data = generate_pdf(result_obj)
            st.download_button(
                "Download PDF Report",
                data=pdf_data,
                file_name=f"procurement_{category}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

            rfq_text = generate_all_rfq_drafts(result_obj, hotel_name=profile.name or "Our Hotel Project")
            st.download_button(
                "Download RFQ Drafts",
                data=rfq_text,
                file_name=f"rfq_{category}.txt",
                mime="text/plain",
                use_container_width=True,
            )


def render_main() -> None:
    st.title("Hotel Procurement Research Tool")
    st.caption("No paid APIs · Multi-agent · Luxury 5-star focus · Europe")

    if not st.session_state.last_result:
        st.info("Set up your hotel profile and run a research request from the sidebar to begin.")
        return

    result = st.session_state.last_result
    products = result.products
    benchmarks = result.hotel_benchmarks
    briefs = result.negotiation_briefs
    req = result.request

    tabs = st.tabs([
        "Dashboard",
        "Product Deep Dive",
        "Hotel Benchmark",
        "Supplier Map",
        "Negotiation Briefs",
        "About / Methodology",
    ])

    with tabs[0]:
        render_dashboard(result)

    with tabs[1]:
        st.header("Product Deep Dive")
        if products:
            selected = st.selectbox(
                "Select a product",
                options=products,
                format_func=lambda p: f"{p.brand} {p.name} — {p.display_price}",
            )
            if selected:
                render_product_card(selected)

    with tabs[2]:
        st.header("Hotel Benchmark")
        st.write(f"Leading hotels specifying brands for **{req.category}**:")
        if benchmarks:
            for b in benchmarks:
                st.markdown(f"- **{b.hotel_name}** ({b.tier}) — {b.brand}")
        else:
            st.info("No curated hotel benchmark data for this category yet.")

    with tabs[3]:
        st.header("Supplier Map")
        suppliers_seen = {}
        for p in products:
            if p.supplier and p.supplier.name not in suppliers_seen:
                suppliers_seen[p.supplier.name] = p.supplier
        if suppliers_seen:
            for s in suppliers_seen.values():
                st.markdown(
                    f"- **[{s.name}]({s.website})** · {s.country} · "
                    f"Service: {', '.join(s.service_countries) or 'N/A'} · "
                    f"Certs: {', '.join(s.certifications) or 'N/A'}"
                )
        else:
            st.info("No supplier data available.")

    with tabs[4]:
        st.header("Negotiation Briefs")
        for brief in briefs:
            with st.container(border=True):
                st.subheader(f"{brief.supplier_name}")
                st.markdown(f"**Product:** {brief.product_name}")
                st.markdown(f"**Market position:** {brief.market_position}")
                if brief.target_price_eur:
                    st.markdown(f"**Suggested target price:** €{brief.target_price_eur:,.2f}")
                if brief.alternatives:
                    st.markdown("**Alternatives:** " + ", ".join(brief.alternatives))
                if brief.leverage_points:
                    st.markdown("**Leverage points:**")
                    for lp in brief.leverage_points:
                        st.markdown(f"- {lp}")
                if brief.suggested_terms:
                    st.markdown("**Suggested terms:**")
                    for t in brief.suggested_terms:
                        st.markdown(f"- {t}")

    with tabs[5]:
        st.header("About / Methodology")
        st.markdown(
            """
            **Scoring methodology**

            Every product is scored across six dimensions (0-100):
            - **Quality:** brand tier, spec completeness, warranty, review sentiment
            - **Value:** quality per euro, benchmarked against category median
            - **Rarity:** inverse of global/hotel presence and distribution breadth
            - **Exclusivity:** rarity + boutique coefficient + competitor usage
            - **TCO:** 10-year total cost of ownership (price + energy + maintenance + replacement)
            - **Compliance:** CE marking, energy labels, warranty adequacy

            Weights are tuned per category. No paid APIs are used by default; all agents run locally
            using curated datasets, heuristics, and polite web scraping.

            **Data sources**
            - Curated hotel brand standards (`data/hotel_brands.json`)
            - Curated European hospitality supplier index (`data/supplier_index.json`)
            - Seed product database (`data/sample_products.json`)
            - Public manufacturer websites (cached, rate-limited)

            **Limitations**
            - Prices are estimates or list prices; actual quotes require supplier negotiation.
            - Live scraping depends on website availability and robots policies.
            - Scores reflect our curated model; weights can be adjusted in the taxonomy file.
            """
        )


def main() -> None:
    init_session_state()
    render_sidebar()
    render_main()


if __name__ == "__main__":
    main()
