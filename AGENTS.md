# Hotel Procurement Research Tool — Agent Context

## Project Overview

**Name:** Hotel Procurement Research Tool  
**Purpose:** Multi-agent procurement research co-pilot for a luxury 5-star hotel build in Europe. Helps research, rank, and source guest-room appliances, AV, bathroom amenities, and back-of-house/F&B equipment.  
**Working Dir:** `/home/kfiftysix/hotel-procure/`  
**UI:** Streamlit web app at `http://localhost:8501`  
**Run:** `./run.sh` or `streamlit run app.py`

## Constraints

- **Live search only — no static product catalog.** Products must come from `LiveSearchAgent`
  (Serper.dev search), never a hardcoded JSON product list. (A `data/sample_products.json`
  catalog used to exist and was the root problem with an earlier version of this tool — it made
  the app look like a search engine while only ever returning ~45 pre-seeded items. Don't reintroduce it.)
- **One paid API dependency, explicitly approved by the user: Serper.dev** (Google Search API,
  used for both organic and Shopping results). Requires `SERPER_API_KEY` in `.env` (see `.env.example`).
  Don't add further paid APIs (OpenAI, Anthropic, etc.) without explicit user approval.
- Direct scraping of Google/Bing/DuckDuckGo does NOT work from a plain HTTP client — confirmed
  via testing, they return CAPTCHA/anomaly challenges to non-browser clients. That's why Serper exists.
- Many B2B/hospitality supplier sites are Cloudflare-protected or JS-rendered and can't be scraped
  with the plain `requests`-based `PoliteClient`; `LiveSearchAgent` treats failures as skip, not fatal.
- Europe-focused: CE, 220–240 V, energy labels, local warranty/service networks.
- Luxury 5-star positioning: rarity, design coherence, and guest experience matter.

## Architecture

```
app.py                  # Streamlit entry point
agents/
  orchestrator.py       # Dispatches requests to category specialists
  category/             # Appliances, AV, Bathroom, BackOfHouse, Generalist — get_products() calls LiveSearchAgent
  research/             # live_search (Serper-backed discovery), hotel_benchmark, review_sentiment
  analysis/             # SupplierCrossCheck, Exclusivity, QualityPrice, TCO, Compliance, NegotiationBrief
core/
  models.py             # Dataclasses: Product, Supplier, ResearchResult, etc.
  cache.py              # SQLite cache with TTL (also caches Serper responses, to avoid burning paid quota)
  config.py             # Constants, UA list, rate limits, SERPER_API_KEY (loaded from .env)
  scoring.py            # Composite scoring engine
  data_loader.py        # JSON dataset loaders (taxonomy, hotel brands, supplier index — reference data only)
scraping/
  serper.py             # Serper.dev API client (organic + shopping search), cached
  client.py             # Polite HTTP client with caching and rate limiting, for fetching candidate pages
  parsers.py            # HTML/text extraction helpers
  extractors.py         # Generic manufacturer spec-page extractor
ui/
  dashboard.py          # Ranked product table + filters
  product_card.py       # Detailed product renderer
  reports.py            # CSV + PDF generators
  rfq.py                # RFQ email draft generator
data/
  category_taxonomy.json   # scoring weights, brand tiers — reference data
  hotel_brands.json        # reference data
  supplier_index.json      # used to scope/prioritise live search by category, NOT a product catalog
tests/
  test_scoring.py
  test_agents.py
  test_live_search.py
  test_scrapers.py
```

## Key Data Models

- `Product` — brand, specs, price, supplier, scores (quality, value, rarity, exclusivity, TCO, compliance, overall)
- `Supplier` — name, country, website, service_countries, certifications
- `HotelBenchmark` — hotel, tier, category, brand
- `ResearchRequest` — category, quantity, budget, design_brief, must_haves
- `ResearchResult` — products, benchmarks, negotiation briefs

## Scoring

Weights are category-specific and live in `data/category_taxonomy.json`. Default weights:

| Category | Quality | Value | Rarity | Exclusivity | TCO | Compliance |
|----------|---------|-------|--------|-------------|-----|------------|
| appliances | 0.30 | 0.20 | 0.15 | 0.10 | 0.15 | 0.10 |
| av | 0.25 | 0.20 | 0.20 | 0.10 | 0.15 | 0.10 |
| bathroom | 0.25 | 0.15 | 0.25 | 0.20 | 0.10 | 0.05 |
| back_of_house | 0.30 | 0.20 | 0.10 | 0.05 | 0.25 | 0.10 |
| general | 0.25 | 0.25 | 0.15 | 0.10 | 0.15 | 0.10 |

## Development

**Python:** 3.13 venv  
**Dependencies:** streamlit, requests, beautifulsoup4, lxml, trafilatura, pandas, reportlab, rapidfuzz, playwright, python-dotenv, pytest
**Secrets:** `SERPER_API_KEY` in `.env` (copy `.env.example`), get a free key at https://serper.dev

**Run tests:**
```bash
cd /home/kfiftysix/hotel-procure
source venv/bin/activate
python -m pytest tests/ -v
```

**Launch app:**
```bash
./run.sh
```

## Adding New Brands or Suppliers

1. Add brand rarity metadata to `data/category_taxonomy.json` under `brand_rarity` (affects
   exclusivity scoring once a brand is found live — this does not seed products).
2. Add supplier to `data/supplier_index.json` with `specialties` matching category/subcategory
   keys — this scopes which suppliers get `site:`-restricted organic search.
3. Re-run tests and verify with the Streamlit UI.

## Known Limitations

- Prices come from Google Shopping when available; many B2B/hospitality sites are quote-on-request
  and never show a public price — those products show "Price on request."
- Coverage varies per search: some supplier sites block automated requests outright (Cloudflare),
  others are JS-rendered and not fetchable by the plain HTTP client.
- Scoring weights reflect a luxury-Europe model; adjust taxonomy for other positioning.
- No persistent user accounts; state is per-browser session.
- Serper.dev responses are cached (`cache.db`) to limit paid API usage; delete `cache.db` to force
  fresh searches.
