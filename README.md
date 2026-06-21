# Hotel Procurement Research Tool

A multi-agent Streamlit web application for researching and ranking hospitality products for luxury hotel projects in Europe. Built without paid APIs — all agents run locally using curated datasets, heuristics, and polite web scraping.

## What it does

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
playwright install chromium
streamlit run app.py
```

Or simply run:

```bash
./run.sh
```

Then open http://localhost:8501 in your browser.

## Running tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

## Architecture

```
hotel-procure/
├── app.py                  # Streamlit UI
├── agents/                 # Specialist and analysis agents
│   ├── orchestrator.py
│   ├── category/           # Appliances, AV, Bathroom, BOH, Generalist
│   ├── research/           # Web scout, hotel benchmark, marketplace, reviews
│   └── analysis/           # Supplier, exclusivity, quality-price, TCO, compliance, negotiation
├── core/                   # Models, cache, scoring, data loader
├── scraping/               # Polite HTTP client, parsers, extractors
├── ui/                     # Dashboard, product card, reports, RFQ
├── data/                   # Curated datasets (JSON)
└── tests/                  # pytest suite
```

## No paid APIs

The tool works offline using the curated datasets in `data/`. Live web scraping is available but rate-limited and cached; no OpenAI, Google, or other paid keys are required.

## Data sources

- `data/category_taxonomy.json` — category weights, brand tiers, spec priorities
- `data/hotel_brands.json` — leading luxury hotels and known amenity brands
- `data/supplier_index.json` — European hospitality suppliers and distributors
- `data/sample_products.json` — seed product database with specs and estimated prices
- Public manufacturer websites (cached, polite scraping)

## Customisation

Edit `data/category_taxonomy.json` to adjust scoring weights, brand tiers, or add new brands. Add products to `data/sample_products.json` to expand the seed database.

## License

Private project for personal hotel procurement research.
