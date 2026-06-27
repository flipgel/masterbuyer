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
from ui.intro import render_intro
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


BRAND_PRODUCT_TYPES = [
    "All products",
    "Glassware",
    "Tableware & Crockery",
    "Cutlery & Flatware",
    "Textiles & Linens",
    "Bathroom accessories",
    "Kitchen equipment",
    "Decoration & Homeware",
]


def init_session_state() -> None:
    defaults = {
        "hotel_profile": HotelProfile(),
        "last_result": None,
        "last_query": "",
        "search_mode": "product",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_data(ttl=3600)
def run_research(
    category: str, query: str, quantity: int, budget: float | None, must_have: str,
    brand_mode: bool = False,
) -> ResearchResult:
    """Run live research and return a ResearchResult object (cached via pickle)."""
    request = ResearchRequest(
        category=category,
        quantity=quantity,
        budget_per_unit_eur=budget if budget and budget > 0 else None,
        query=query,
        design_brief=query,
        must_have=[x.strip() for x in must_have.split(",") if x.strip()],
        brand_mode=brand_mode,
    )
    orchestrator = OrchestratorAgent()
    return orchestrator.run(request)


def do_search(
    query: str,
    quantity: int = 50,
    budget: float | None = None,
    must_have: str = "",
    display_query: str | None = None,
    brand_mode: bool = False,
) -> None:
    category = infer_category(query)
    with st.spinner("Searching live supplier sites and the web..."):
        try:
            result = run_research(category, query, quantity, budget, must_have, brand_mode)
        except SerperConfigError as e:
            st.error(str(e))
            return
        except Exception as e:
            st.error(f"Search failed: {e}")
            return
    st.session_state.last_result = result
    st.session_state.last_query = display_query if display_query is not None else query
    st.session_state.brand_mode_active = brand_mode
    # Reset filters so they don't bleed into a new search's product set
    st.session_state.pop("filter_initialised", None)


def render_search_bar() -> None:
    mode_index = 1 if st.session_state.get("search_mode") == "brand" else 0
    mode = st.radio(
        "Search by",
        ["Product", "Brand catalog"],
        index=mode_index,
        horizontal=True,
        label_visibility="collapsed",
    )
    is_brand = mode == "Brand catalog"

    with st.form("search_form", clear_on_submit=False):
        cols = st.columns([5, 1])
        with cols[0]:
            placeholder = (
                "e.g. Pasabahce, Villeroy & Boch, Riedel, Frette..."
                if is_brand
                else "e.g. kettle, minibar fridge, brass bathroom faucet..."
            )
            query = st.text_input(
                "Search",
                value=st.session_state.last_query,
                placeholder=placeholder,
                label_visibility="collapsed",
            )
        with cols[1]:
            submitted = st.form_submit_button("Search", type="primary", use_container_width=True)

        product_type = "All products"
        if is_brand:
            product_type = st.selectbox(
                "Product type (optional)",
                BRAND_PRODUCT_TYPES,
                label_visibility="collapsed",
            )

    if submitted and query.strip():
        brand_name = query.strip()
        if is_brand:
            st.session_state.search_mode = "brand"
            type_hint = (
                "" if product_type == "All products"
                else f" {product_type.split('&')[0].strip().lower()}"
            )
            effective_query = f"{brand_name}{type_hint}"
        else:
            st.session_state.search_mode = "product"
            effective_query = brand_name
        do_search(effective_query, display_query=brand_name, brand_mode=is_brand)
        st.rerun()


def render_landing() -> None:
    render_intro()
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


_IMG_PLACEHOLDER = (
    "<div style='width:70px;height:70px;border-radius:6px;background:#F0EDE8;"
    "display:flex;align-items:center;justify-content:center;"
    "font-size:28px;color:#C8C4BC;'>📦</div>"
)


_OFFICIAL_BADGE = (
    "<span style='display:inline-block; padding:1px 7px; border-radius:3px;"
    " background:#0D0D0D; color:#fff; font-family:Syne,sans-serif;"
    " font-weight:800; font-size:11px; letter-spacing:0.03em;'>OFFICIAL</span>"
)


def render_result_row(product, rank: int, hotel_name: str) -> None:
    with st.container(border=True):
        cols = st.columns([1, 4, 2, 1, 2])
        with cols[0]:
            if product.image_url:
                render_product_image(product.image_url, width=80)
            else:
                st.markdown(_IMG_PLACEHOLDER, unsafe_allow_html=True)
        with cols[1]:
            badge = _rank_badge(rank)
            name = f"[{product.brand} — {product.name}]({product.source_url})" if product.source_url else f"{product.brand} — {product.name}"
            official = f" &nbsp; {_OFFICIAL_BADGE}" if product.is_official_source else ""
            st.markdown(
                f"{badge} &nbsp; **{name}**{official}",
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


def _init_filter_state(products: list) -> None:
    """Set filter defaults once per search (not on every rerun)."""
    if "filter_initialised" not in st.session_state:
        prices = [p.effective_price for p in products if p.effective_price is not None]
        st.session_state.filter_initialised = True
        st.session_state.f_brand = []
        st.session_state.f_min_score = 0
        st.session_state.f_max_price = round((max(prices) * 1.1) if prices else 1000.0, 2)
        st.session_state.f_sort_by = "overall_score"


SORT_OPTIONS = ["overall_score", "quality_score", "value_score", "exclusivity_score", "tco_score"]


def render_filters(products: list) -> list:
    """Filter bar with an explicit Apply button so selections actually commit."""
    _init_filter_state(products)

    with st.form("filter_form"):
        cols = st.columns([2, 2, 2, 2])
        with cols[0]:
            brand_sel = st.multiselect(
                "Brand",
                options=sorted({p.brand for p in products}),
                default=st.session_state.f_brand,
            )
        with cols[1]:
            score_sel = st.slider("Min score", 0, 100, value=st.session_state.f_min_score)
        with cols[2]:
            price_sel = st.number_input(
                "Max price (EUR)",
                min_value=0.0,
                value=st.session_state.f_max_price,
                step=10.0,
            )
        with cols[3]:
            sort_sel = st.selectbox(
                "Sort by",
                SORT_OPTIONS,
                index=SORT_OPTIONS.index(st.session_state.f_sort_by),
            )
        apply = st.form_submit_button("Apply filters", use_container_width=True, type="primary")

    if apply:
        st.session_state.f_brand = brand_sel
        st.session_state.f_min_score = score_sel
        st.session_state.f_max_price = price_sel
        st.session_state.f_sort_by = sort_sel

    # Always filter/sort by committed values in session_state
    filtered = [p for p in products if p.overall_score >= st.session_state.f_min_score]
    if st.session_state.f_brand:
        filtered = [p for p in filtered if p.brand in st.session_state.f_brand]
    filtered = [
        p for p in filtered
        if p.effective_price is None or p.effective_price <= st.session_state.f_max_price
    ]
    return sorted(filtered, key=lambda p: getattr(p, st.session_state.f_sort_by), reverse=True)


def render_results() -> None:
    result = st.session_state.last_result
    if not result.products:
        st.warning("No live results found for this search — try a broader query.")
        render_diagnostics(result.diagnostics)
        return

    hotel_name = st.session_state.hotel_profile.name or "Our Hotel Project"
    render_diagnostics(result.diagnostics)

    is_brand = st.session_state.get("brand_mode_active", False)
    if is_brand:
        # Official source pinned first, then resellers sorted cheapest first.
        official = [p for p in result.products if p.is_official_source]
        resellers = sorted(
            [p for p in result.products if not p.is_official_source],
            key=lambda p: p.effective_price if p.effective_price is not None else float("inf"),
        )
        filtered_products = official + resellers
        st.caption(
            f"{len(official)} official source · {len(resellers)} resellers sorted cheapest first"
        )
        for i, product in enumerate(filtered_products, 1):
            render_result_row(product, i, hotel_name)
    else:
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
