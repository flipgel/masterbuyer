"""masterbuyer — live hotel procurement search engine. Streamlit entry point."""
import streamlit as st

from agents.orchestrator import OrchestratorAgent
from core.cache import cache
from core.config import get_secret
from core.models import HotelProfile, ResearchRequest, ResearchResult
from core.query_intent import infer_category
from core.scoring import score_to_grade
from scraping.serper import SerperConfigError
from ui.dashboard import render_dashboard
from ui.images import render_product_image
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
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800;900&family=Outfit:wght@400;500;600&display=swap');
    :root {
        --ink:     #0D0D0D;
        --bg:      #F7F4EF;
        --surface: #FFFFFF;
        --accent:  #FF4500;
        --accent2: #5B2EFF;
        --muted:   #7A7670;
        --border:  #D9D4CC;
        --grade-a: #00B87A;
        --grade-b: #3B9EFF;
        --grade-c: #F5A623;
        --grade-d: #FF6B35;
        --grade-f: #E82C2C;
    }

    /* ── typography ── */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif !important;
    }
    h1, h2, h3 {
        font-family: 'Syne', sans-serif !important;
        font-weight: 800 !important;
        color: var(--ink) !important;
        letter-spacing: -0.03em !important;
    }

    /* ── page background — subtle crosshatch ── */
    .main {
        background-color: var(--bg) !important;
        background-image:
            linear-gradient(rgba(13,13,13,.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(13,13,13,.04) 1px, transparent 1px) !important;
        background-size: 28px 28px !important;
    }
    .main .block-container {
        background: transparent !important;
        max-width: 940px !important;
        padding-top: 2rem !important;
    }

    /* ── cards — left accent stripe ── */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface) !important;
        border: 1.5px solid var(--border) !important;
        border-left: 4px solid var(--accent) !important;
        border-radius: 3px !important;
        box-shadow: 3px 3px 0px var(--border) !important;
    }

    /* ── buttons ── */
    .stButton>button {
        background: var(--ink) !important;
        color: #fff !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        border: 2px solid var(--ink) !important;
        border-radius: 3px !important;
        letter-spacing: 0.01em !important;
        transition: background 0.15s, transform 0.1s !important;
    }
    .stButton>button:hover {
        background: var(--accent) !important;
        border-color: var(--accent) !important;
        transform: translate(-1px, -1px) !important;
    }

    /* ── link buttons ── */
    [data-testid="stLinkButton"] a {
        background: var(--surface) !important;
        color: var(--ink) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 3px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stLinkButton"] a:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }

    /* ── expanders ── */
    [data-testid="stExpander"] summary {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        color: var(--muted) !important;
    }
    [data-testid="stExpander"] summary:hover { color: var(--ink) !important; }

    /* ── search input ── */
    input[aria-label="Search"] {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.1rem !important;
        border: 2px solid var(--ink) !important;
        border-radius: 3px !important;
    }

    /* ── captions ── */
    .stCaption { color: var(--muted) !important; font-size: 0.8rem !important; }

    /* ── hide all Streamlit chrome (toolbar, deploy, manage) ── */
    [data-testid="collapsedControl"],
    [data-testid="stToolbar"],
    [data-testid="manage-app-button"],
    [data-testid="stDeployButton"],
    [data-testid="stStatusWidget"],
    .stDeployButton,
    #MainMenu,
    header[data-testid="stHeader"] { display: none !important; }

    /* ── metric labels ── */
    [data-testid="stMetricLabel"] { font-size: 0.7rem !important; color: var(--muted) !important; }
    [data-testid="stMetricValue"] { font-family: 'Syne', sans-serif !important; font-weight: 700 !important; }

    /* ──────────────────────────────────────────
       iOS / MOBILE
       ────────────────────────────────────────── */

    /* Prevent iOS auto-zoom on input focus (requires ≥ 16px) */
    input, select, textarea {
        font-size: 16px !important;
    }

    /* Ensure tap targets meet Apple HIG minimum (44 × 44 pt) */
    .stButton>button,
    [data-testid="stLinkButton"] a {
        min-height: 44px !important;
        padding: 0 16px !important;
    }

    /* Remove hover transform on touch devices (avoids stuck states) */
    @media (hover: none) {
        .stButton>button:hover {
            background: var(--ink) !important;
            border-color: var(--ink) !important;
            transform: none !important;
        }
    }

    /* ── Phone layout (≤ 640 px) ── */
    @media (max-width: 640px) {
        /* Tighten page padding on small screens */
        .main .block-container {
            padding-left: 12px !important;
            padding-right: 12px !important;
            padding-top: 1rem !important;
        }

        /* Result cards: stack the five columns into two rows
           (image+name on top, price+grade+email below) */
        [data-testid="stVerticalBlockBorderWrapper"]
        > div > div > [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]
        > div > div > [data-testid="stHorizontalBlock"]
        > [data-testid="stColumn"]:nth-child(1) {
            flex: 0 0 20% !important; min-width: 20% !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]
        > div > div > [data-testid="stHorizontalBlock"]
        > [data-testid="stColumn"]:nth-child(2) {
            flex: 0 0 80% !important; min-width: 80% !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]
        > div > div > [data-testid="stHorizontalBlock"]
        > [data-testid="stColumn"]:nth-child(3),
        [data-testid="stVerticalBlockBorderWrapper"]
        > div > div > [data-testid="stHorizontalBlock"]
        > [data-testid="stColumn"]:nth-child(4) {
            flex: 0 0 33% !important; min-width: 33% !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]
        > div > div > [data-testid="stHorizontalBlock"]
        > [data-testid="stColumn"]:nth-child(5) {
            flex: 0 0 34% !important; min-width: 34% !important;
        }

        /* Filter bar: 2-per-row grid */
        [data-testid="stHorizontalBlock"]:has(
            [data-testid="stMultiSelect"]
        ) > [data-testid="stColumn"] {
            flex: 0 0 50% !important; min-width: 50% !important;
        }

        /* Score metrics: smaller on mobile */
        [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
    }
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
        except Exception as e:
            st.error(f"Search failed: {e}")
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
    st.markdown("<div style='height:clamp(16px,5vh,10vh)'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='text-align:center; margin-bottom:4px; white-space:nowrap;'>
            <span style='font-family:Syne,sans-serif;
                         font-size:clamp(28px,8.5vw,90px); font-weight:900;
                         color:#0D0D0D; letter-spacing:-0.05em; line-height:1;'>master</span><span
                  style='font-family:Syne,sans-serif;
                         font-size:clamp(28px,8.5vw,90px); font-weight:900;
                         color:#FF4500; letter-spacing:-0.05em; line-height:1;'>buyer</span>
        </div>
        <p style='text-align:center; font-family:Outfit,sans-serif; color:#7A7670;
                  font-size:1rem; margin-top:6px; letter-spacing:0.05em;'>
            yes Irina, <em>masterbuyer.</em>
        </p>
        """,
        unsafe_allow_html=True,
    )
    render_search_bar()
    if not get_secret("SERPER_API_KEY"):
        st.error(
            "SERPER_API_KEY is not configured — live search will not work until it's "
            "set (Streamlit Cloud: Settings → Secrets)."
        )


_GRADE_COLORS = {
    "A+": "#00B87A", "A": "#00B87A",
    "B": "#3B9EFF",
    "C": "#F5A623",
    "D": "#FF6B35",
    "F": "#E82C2C",
}


def _rank_badge(n: int) -> str:
    return (
        f"<span style='display:inline-flex; align-items:center; justify-content:center;"
        f" width:28px; height:28px; border-radius:50%; background:#0D0D0D; color:#fff;"
        f" font-family:Syne,sans-serif; font-weight:900; font-size:12px;'>{n}</span>"
    )


def _grade_pill(score: float) -> str:
    grade = score_to_grade(score)
    color = _GRADE_COLORS.get(grade, "#888")
    return (
        f"<span style='display:inline-block; padding:2px 8px; border-radius:3px;"
        f" background:{color}; color:#fff; font-family:Syne,sans-serif;"
        f" font-weight:800; font-size:13px;'>{grade}</span>"
        f"<span style='color:#7A7670; font-size:11px; margin-left:4px;'>{score:.0f}</span>"
    )


def render_result_row(product, rank: int, hotel_name: str) -> None:
    with st.container(border=True):
        cols = st.columns([1, 4, 2, 1, 2])
        with cols[0]:
            render_product_image(product.image_url, width=80)
        with cols[1]:
            badge = _rank_badge(rank)
            name = f"[{product.brand} — {product.name}]({product.source_url})" if product.source_url else f"{product.brand} — {product.name}"
            st.markdown(
                f"{badge} &nbsp; **{name}**",
                unsafe_allow_html=True,
            )
            st.caption(product.subcategory.title())
        with cols[2]:
            st.markdown(
                f"<span style='font-family:Syne,sans-serif; font-weight:700; font-size:1.05rem;'>{product.display_price}</span>",
                unsafe_allow_html=True,
            )
        with cols[3]:
            st.markdown(_grade_pill(product.overall_score), unsafe_allow_html=True)
        with cols[4]:
            mailto = build_mailto_link(product, hotel_name)
            st.link_button("✉️ Inquiry email", mailto, use_container_width=True)

        with st.expander("Details"):
            render_product_card(product, rank=rank)


def render_diagnostics(diag: dict) -> None:
    if not diag:
        return
    with st.expander("🩺 Search diagnostics", expanded=not st.session_state.last_result.products):
        st.json(diag)


def render_filters(products: list) -> list:
    """Compact filter bar above the results list. Returns the filtered+sorted list."""
    prices = [p.effective_price for p in products if p.effective_price is not None]
    default_max_price = (max(prices) * 1.1) if prices else 1000.0

    cols = st.columns([2, 2, 2, 2])
    with cols[0]:
        brand_filter = st.multiselect(
            "Brand", options=sorted({p.brand for p in products}), key="main_filter_brand"
        )
    with cols[1]:
        min_score = st.slider("Min overall score", 0, 100, 0, key="main_filter_min_score")
    with cols[2]:
        max_price = st.number_input(
            "Max price (EUR)", min_value=0.0, value=default_max_price, step=10.0, key="main_filter_max_price"
        )
    with cols[3]:
        sort_by = st.selectbox(
            "Sort by",
            ["overall_score", "quality_score", "value_score", "exclusivity_score", "tco_score"],
            key="main_filter_sort_by",
        )

    filtered = [p for p in products if p.overall_score >= min_score]
    if brand_filter:
        filtered = [p for p in filtered if p.brand in brand_filter]
    filtered = [p for p in filtered if p.effective_price is None or p.effective_price <= max_price]
    return sorted(filtered, key=lambda p: getattr(p, sort_by), reverse=True)


def render_results() -> None:
    result = st.session_state.last_result
    if not result.products:
        st.warning("No live results found for this search — try a broader query.")
        render_diagnostics(result.diagnostics)
        return

    hotel_name = st.session_state.hotel_profile.name or "Our Hotel Project"
    render_diagnostics(result.diagnostics)
    filtered = render_filters(result.products)
    st.caption(f"Showing {len(filtered)} of {len(result.products)} live results, ranked by overall fit for a luxury hotel.")
    for i, product in enumerate(filtered, 1):
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
            ref_cols = st.columns(2)
            with ref_cols[0]:
                if st.button("Re-run with these settings"):
                    do_search(st.session_state.last_query, quantity, budget, must_have)
                    st.rerun()
            with ref_cols[1]:
                if st.button("🔄 Clear cache & retry"):
                    st.cache_data.clear()
                    cache.clear_all()
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
        st.markdown(
            "<span style='font-family:Syne,sans-serif; font-weight:900;"
            " font-size:clamp(1.4rem,5vw,2rem); color:#0D0D0D; letter-spacing:-0.04em;'>master</span>"
            "<span style='font-family:Syne,sans-serif; font-weight:900;"
            " font-size:clamp(1.4rem,5vw,2rem); color:#FF4500; letter-spacing:-0.04em;'>buyer</span>",
            unsafe_allow_html=True,
        )
        render_search_bar()
        render_advanced_panel()
        render_results()


if __name__ == "__main__":
    main()
