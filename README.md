# Hotel Procurement Research Tool

A multi-agent Streamlit web application that **live-searches** for hospitality products
for luxury hotel projects in Europe, then ranks and analyses the real results found.

## What it does

- **Live product search** — every query hits the real web (via the Serper.dev Google
  Search API: organic + Shopping results) and, where reachable, fetches and parses
  manufacturer/supplier pages directly. There is no static product catalog.
- **Category specialists** for guest-room appliances, AV, bathroom accessories, and back-of-house/F&B equipment.
- **Hotel benchmark research** — see what leading luxury hotels specify for comparable items.
- **Supplier cross-check** — map European distributors, service coverage, and certifications.
- **Exclusivity & rarity scoring** — understand how common or boutique a brand is.
- **Quality / price matching** and **10-year TCO** estimates.
- **Compliance checks** — CE marking, energy labels, warranty adequacy.
- **Negotiation briefs** and **RFQ email drafts**.
- **Exports** — CSV, PDF report, and RFQ drafts.

## Quick start

```bash
cd /home/kfiftysix/hotel-procure
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your Serper.dev API key
```

Get a free API key at https://serper.dev (free tier covers light personal use; see
`.env.example` for the variable name). Then:

```bash
./run.sh
```

Or directly:

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Running tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

Tests don't require a live API key or network access — search/fetch calls are mocked.

## Architecture

```
hotel-procure/
├── app.py                  # Streamlit UI
├── agents/                 # Specialist and analysis agents
│   ├── orchestrator.py
│   ├── category/           # Appliances, AV, Bathroom, BOH, Generalist
│   ├── research/           # live_search (Serper-backed), hotel benchmark, reviews
│   └── analysis/           # Supplier, exclusivity, quality-price, TCO, compliance, negotiation
├── core/                   # Models, cache, scoring, data loader, config
├── scraping/                # Serper client, polite HTTP client, parsers, extractors
├── ui/                      # Dashboard, product card, reports, RFQ
├── data/                    # Curated reference datasets (JSON) — not products
└── tests/                   # pytest suite
```

## How search works

1. A free-text query + category go to `LiveSearchAgent` (`agents/research/live_search.py`).
2. **Google Shopping** results (via Serper) give name/price/link/merchant directly — most
   reliable source, but not every category appears in Shopping.
3. **Organic search** scoped to relevant suppliers from `data/supplier_index.json`
   (`site:<supplier domain> ...`) finds manufacturer/spec pages, which are then fetched
   and parsed for extra detail (specs, additional price candidates) when the site allows it.
4. Sites that block automated requests (Cloudflare, etc.) are skipped, not fatal — coverage
   varies by category and what's reachable at search time.
5. Results feed the same exclusivity/quality/TCO/compliance/negotiation analysis agents either way.

## Data sources

- `data/category_taxonomy.json` — category weights, brand tiers, spec priorities
- `data/hotel_brands.json` — leading luxury hotels and known amenity brands
- `data/supplier_index.json` — European hospitality suppliers and distributors (used to
  scope live search, not as a product catalog)
- Live web search (Serper.dev) and manufacturer/supplier pages (cached, rate-limited)

## Customisation

Edit `data/category_taxonomy.json` to adjust scoring weights, brand tiers, or add new brands.
Edit `data/supplier_index.json` to add suppliers that should be prioritised in live search.

## License

Private project for personal hotel procurement research.
