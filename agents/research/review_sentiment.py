"""Review sentiment agent: analyze durability and quality signals."""
import re
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from core.models import ResearchRequest, ReviewSignals
from scraping.extractors import extract_review_snippets


class ReviewSentimentAgent(BaseAgent):
    """Extract review signals from text snippets without paid NLP APIs."""

    name = "review_sentiment"

    POSITIVE_WORDS = [
        "excellent", "amazing", "love", "perfect", "great", "fantastic",
        "quiet", "silent", "reliable", "durable", "robust", "high quality",
        "premium", "worth", "solid", "well built", "long lasting",
    ]
    NEGATIVE_WORDS = [
        "terrible", "awful", "hate", "broke", "broken", "noisy", "loud",
        "cheap", "flimsy", "disappointed", "poor quality", "issue", "problem",
        "returned", "failed", "not worth", "regret",
    ]
    DURABILITY_WORDS = ["durable", "robust", "long lasting", "broke", "broken", "reliable"]
    NOISE_WORDS = ["quiet", "silent", "noisy", "loud", "hum"]
    SERVICE_WORDS = ["warranty", "service", "repair", "support", "customer service"]

    def analyze(self, text: str, source: str = "unknown") -> ReviewSignals:
        if not text:
            return ReviewSignals()

        snippets = extract_review_snippets(text, max_snippets=20)
        positive = sum(1 for s in snippets if s["sentiment"] == "positive")
        negative = sum(1 for s in snippets if s["sentiment"] == "negative")
        total = len(snippets) if snippets else 1

        lower = text.lower()
        durability = sum(1 for w in self.DURABILITY_WORDS if w in lower)
        noise = sum(1 for w in self.NOISE_WORDS if w in lower)
        service = sum(1 for w in self.SERVICE_WORDS if w in lower)

        avg_sentiment = (positive - negative) / total
        if not snippets:
            avg_sentiment = 0.0

        pos_phrases = list(
            set([s["text"] for s in snippets if s["sentiment"] == "positive"])
        )[:5]
        neg_phrases = list(
            set([s["text"] for s in snippets if s["sentiment"] == "negative"])
        )[:5]

        return ReviewSignals(
            source_count=1,
            avg_sentiment=round(max(-1, min(1, avg_sentiment)), 2),
            durability_mentions=durability,
            noise_mentions=noise,
            service_mentions=service,
            positive_phrases=pos_phrases,
            negative_phrases=neg_phrases,
        )

    def analyze_brand(
        self,
        brand: str,
        product_name: str,
        review_texts: Optional[List[str]] = None,
    ) -> ReviewSignals:
        review_texts = review_texts or []
        combined = "\n".join(review_texts)
        return self.analyze(combined, source=f"{brand} {product_name}")

    def run(self, request: ResearchRequest) -> ReviewSignals:
        return self.analyze(request.design_brief)
