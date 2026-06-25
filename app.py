"""masterbuyer — live hotel procurement search engine. Streamlit entry point."""
import streamlit as st

from agents.orchestrator import OrchestratorAgent
from core.models import HotelProfile, ResearchRequest, ResearchResult
from core.query_intent import infer_category
from core.scoring import score_to_grade
from scraping.serper import SerperConfigError
from ui.dashboard import render_dashboard
from ui.inquiry import build_mailto_link
from ui.mascot import render_mascot
from ui.product_card import render_product_card
from ui.reports import generate_csv, generate_pdf
from ui.rfq import generate_all_rfq_drafts

st.set_page_config(
    page_title="masterbuyer",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --hotel-navy: #1E3A5F;
        --hotel-gold: #D4A843;
        --hotel-cream: #FDFCFA;
    }
    .main .block-container { background-color: var(--hotel-cream); max-width: 880px; }
    h1, h2, h3 { color: var(--hotel-navy) !important; font-weight: 700 !important; }
    .stButton>button {
        background-color: var(--hotel-gold) !important;
        color: #1A1A1A !important;
        font-weight: 600 !important;
        border: 2px solid #B88A2E !important;
        border-radius: 6px !important;
    }
    .stButton>button:hover { background-color: #E6BC5C !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session_state() -> None:
    defaults = {
        "hotel_profile": HotelProfile(),
        "last_result": None,
        "last_query": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_data(ttl=3600)
def run_research(
    category: str, query: str, quantity: int, budget: float | None, must_have: str
) -> ResearchResult:
    """Run live research and return a ResearchResult object (cached via pickle)."""
    request = ResearchRequest(
        category=category,
        quantity=quantity,
        budget_per_unit_eur=budget if budget and budget > 0 else None,
        query=query,
        design_brief=query,
        must_have=[x.strip() for x in must_have.split(",") if x.strip()],
    )
    orchestrator = OrchestratorAgent()
    return orchestrator.run(request)


def do_search(query: str, quantity: int = 50, budget: float | None = None, must_have: str = "") -> None:
    category = infer_category(query)
    with st.spinner("Searching live supplier sites and the web..."):
        try:
            result = run_research(category, query, quantity, budget, must_have)
        except SerperConfigError as e:
            st.error(str(e))
            return
    st.session_state.last_result = result
    st.session_state.last_query = query


def render_search_bar() -> None:
    with st.form("search_form", clear_on_submit=False):
        cols = st.columns([5, 1])
        with cols[0]:
            query = st.text_input(
                "Search",
                value=st.session_state.last_query,
                placeholder="e.g. kettle, minibar fridge, brass bathroom faucet...",
                label_visibility="collapsed",
            )
        with cols[1]:
            submitted = st.form_submit_button("Search", type="primary", use_container_width=True)
    if submitted and query.strip():
        do_search(query.strip())
        st.rerun()


def render_landing() -> None:
    st.markdown("<div style='height:14vh'></div>", unsafe_allow_html=True)
    st.markdown(
        "<h1 style='text-align:center; font-size:64px;'>masterbuyer</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#888; font-style:italic;'>yes Irina, masterbuyer.</p>",
        unsafe_allow_html=True,
    )
    render_search_bar()


def render_result_row(product, rank: int, hotel_name: str) -> None:
    with st.container(border=True):
        cols = st.columns([5, 2, 1, 2])
        with cols[0]:
            if product.source_url:
                st.markdown(f"**#{rank} [{product.brand} {product.name}]({product.source_url})**")
            else:
                st.markdown(f"**#{rank} {product.brand} {product.name}**")
            st.caption(product.subcategory.title())
        with cols[1]:
            st.markdown(f"**{product.display_price}**")
        with cols[2]:
            st.markdown(f"**{product.overall_score:.0f}** {score_to_grade(product.overall_score)}")
        with cols[3]:
            mailto = build_mailto_link(product, hotel_name)
            st.link_button("✉️ Inquiry email", mailto, use_container_width=True)

        with st.expander("Details"):
            render_product_card(product, rank=rank)


def render_results() -> None:
    result = st.session_state.last_result
    if not result.products:
        st.warning("No live results found for this search — try a broader query.")
        return

    hotel_name = st.session_state.hotel_profile.name or "Our Hotel Project"
    st.caption(f"Found {len(result.products)} live results, ranked by overall fit for a luxury hotel.")
    for i, product in enumerate(result.products, 1):
        render_result_row(product, i, hotel_name)


def render_advanced_panel() -> None:
    result = st.session_state.last_result
    with st.expander("⚙️ Advanced"):
        profile = st.session_state.hotel_profile
        st.subheader("Hotel profile")
        col1, col2 = st.columns(2)
        with col1:
            profile.name = st.text_input("Hotel project name", value=profile.name)
            profile.city = st.text_input("City", value=profile.city)
            profile.room_count = st.number_input("Room count", min_value=0, value=profile.room_count, step=1)
        with col2:
            profile.location_country = st.text_input("Country", value=profile.location_country or "Europe")
            profile.star_rating = st.selectbox(
                "Star rating / positioning",
                ["5-star luxury", "4-star upscale", "3-star midscale", "Boutique design"],
                index=0,
            )

        if result is not None:
            st.subheader("Refine this search")
            ref_col1, ref_col2 = st.columns(2)
            with ref_col1:
                quantity = st.number_input("Quantity needed", min_value=1, value=result.request.quantity, step=1)
            with ref_col2:
                budget = st.number_input(
                    "Budget per unit (EUR, 0 = no limit)",
                    min_value=0.0,
                    value=result.request.budget_per_unit_eur or 0.0,
                    step=50.0,
                )
            must_have = st.text_input(
                "Must-haves (comma separated)",
                value=", ".join(result.request.must_have),
                placeholder="e.g. CE mark, 5-year warranty",
            )
            if st.button("Re-run with these settings"):
                do_search(st.session_state.last_query, quantity, budget, must_have)
                st.rerun()

            st.subheader("Full results table")
            render_dashboard(result)

            st.subheader("Export")
            csv_data = generate_csv(result)
            st.download_button("Download CSV", data=csv_data, file_name="procurement_results.csv", mime="text/csv")
            pdf_data = generate_pdf(result)
            st.download_button("Download PDF Report", data=pdf_data, file_name="procurement_report.pdf", mime="application/pdf")
            rfq_text = generate_all_rfq_drafts(result, hotel_name=profile.name or "Our Hotel Project")
            st.download_button("Download RFQ Drafts", data=rfq_text, file_name="rfq_drafts.txt", mime="text/plain")


def main() -> None:
    init_session_state()
    render_mascot()

    if st.session_state.last_result is None:
        render_landing()
    else:
        st.markdown("<h2 style='text-align:left;'>masterbuyer</h2>", unsafe_allow_html=True)
        render_search_bar()
        render_results()
        render_advanced_panel()


if __name__ == "__main__":
    main()
