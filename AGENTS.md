# Hotel Procurement Research Tool — Agent Context

## Project Overview

**Name:** Hotel Procurement Research Tool  
**Purpose:** Multi-agent procurement research co-pilot for a luxury 5-star hotel build in Europe. Helps research, rank, and source guest-room appliances, AV, bathroom amenities, and back-of-house/F&B equipment.  
**Working Dir:** `/home/kfiftysix/hotel-procure/`  
**UI:** Streamlit web app at `http://localhost:8501`  
**Run:** `./run.sh` or `streamlit run app.py`

## Constraints

- **No paid APIs.** Do not add OpenAI, Anthropic, Google Search, or other metered API dependencies without explicit user approval.
- Deterministic agents using curated JSON datasets, heuristics, and polite web scraping.
- Optional local LLM hook (Ollama) is acceptable but must be strictly optional.
- Europe-focused: CE, 220–240 V, energy labels, local warranty/service networks.
- Luxury 5-star positioning: rarity, design coherence, and guest experience matter.

## Architecture

```
app.py                  # Streamlit entry point
agents/
  orchestrator.py       # Dispatches requests to category specialists
  category/             # Appliances, AV, Bathroom, BackOfHouse, Generalist
  research/             # WebScout, HotelBenchmark, Marketplace, ReviewSentiment
  analysis/             # SupplierCrossCheck, Exclusivity, QualityPrice, TCO, Compliance, NegotiationBrief
core/
  models.py             # Dataclasses: Product, Supplier, ResearchResult, etc.
  cache.py              # SQLite cache with TTL
  config.py             # Constants, UA list, rate limits
  scoring.py            # Composite scoring engine
  data_loader.py        # JSON dataset loaders
scraping/
  client.py             # Polite HTTP client with caching and rate limiting
  parsers.py            # HTML/text extraction helpers
  extractors.py         # Site-specific extractors
ui/
  dashboard.py          # Ranked product table + filters
  product_card.py       # Detailed product renderer
  reports.py            # CSV + PDF generators
  rfq.py                # RFQ email draft generator
data/
  category_taxonomy.json
  hotel_brands.json
  supplier_index.json
  sample_products.json
tests/
  test_scoring.py
  test_agents.py
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
**Dependencies:** streamlit, requests, beautifulsoup4, lxml, trafilatura, pandas, reportlab, rapidfuzz, playwright, pytest

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

## Adding New Products or Brands

1. Add brand rarity metadata to `data/category_taxonomy.json` under `brand_rarity`.
2. Add product entry to `data/sample_products.json` with specs, price, certifications, hotel_usage, pros/cons.
3. Add supplier to `data/supplier_index.json` if applicable.
4. Re-run tests and verify with the Streamlit UI.

## Known Limitations

- Prices are estimates/list prices; final quotes require supplier negotiation.
- Live scraping is polite and cached; some sites may block it.
- Scoring weights reflect a luxury-Europe model; adjust taxonomy for other positioning.
- No persistent user accounts; state is per-browser session.
