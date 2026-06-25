"""Application configuration."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
CACHE_PATH = PROJECT_ROOT / "cache.db"


def _get_secret(name: str, default: str = "") -> str:
    """Read a secret from the environment (.env locally) or st.secrets (Streamlit Cloud)."""
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st

        return st.secrets.get(name, default)
    except Exception:
        return default


# Serper.dev (Google Search API) key for live product discovery.
# Get one at https://serper.dev — set in .env locally, or as a Streamlit Cloud secret.
SERPER_API_KEY = _get_secret("SERPER_API_KEY")

# User-agent rotation for polite scraping
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

# Rate limiting: seconds between requests to the same domain
MIN_DELAY_SECONDS = 1.0
MAX_REQUESTS_PER_MINUTE = 30

# Cache TTLs
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days for general web data
CACHE_TTL_SHORT_SECONDS = 60 * 60       # 1 hour for volatile data

# Default currency
CURRENCY = "EUR"

# Scoring weights per category are loaded from data/category_taxonomy.json
DEFAULT_SCORE_WEIGHTS = {
    "rarity": 0.20,
    "quality": 0.25,
    "value": 0.20,
    "tco": 0.15,
    "exclusivity": 0.15,
    "compliance": 0.05,
}

# Hotel brand tiers for benchmarking
HOTEL_TIERS = ["budget", "midscale", "upscale", "luxury"]
