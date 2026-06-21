"""Polite HTTP client with caching, retries, and rate limiting."""
import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.cache import cache
from core.config import MAX_REQUESTS_PER_MINUTE, MIN_DELAY_SECONDS, USER_AGENTS


@dataclass
class FetchResult:
    url: str
    status_code: int
    headers: Dict[str, str]
    text: str
    elapsed_ms: int
    from_cache: bool
    fetched_at: datetime


class PoliteClient:
    """HTTP client that caches responses and enforces per-domain rate limits."""

    def __init__(
        self,
        min_delay: float = MIN_DELAY_SECONDS,
        max_per_minute: int = MAX_REQUESTS_PER_MINUTE,
        timeout: int = 30,
        retries: int = 3,
    ):
        self.min_delay = min_delay
        self.max_per_minute = max_per_minute
        self.timeout = timeout
        self._session = requests.Session()
        self._last_request: Dict[str, float] = {}
        self._request_times: Dict[str, list] = {}

        retry_strategy = Retry(
            total=retries,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

    def _domain(self, url: str) -> str:
        return urlparse(url).netloc.lower()

    def _wait_if_needed(self, domain: str) -> None:
        now = time.time()

        # Enforce minimum delay since last request to same domain
        last = self._last_request.get(domain)
        if last is not None:
            elapsed = now - last
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)

        # Enforce max requests per minute sliding window
        window = self._request_times.setdefault(domain, [])
        cutoff = now - 60
        recent = [t for t in window if t > cutoff]
        if len(recent) >= self.max_per_minute:
            sleep_for = 60 - (now - recent[0]) + 0.5
            if sleep_for > 0:
                time.sleep(sleep_for)
            recent = [t for t in recent if t > time.time() - 60]
        recent.append(time.time())
        self._request_times[domain] = recent

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def get(
        self,
        url: str,
        ttl_seconds: Optional[int] = None,
        use_cache: bool = True,
        allow_redirects: bool = True,
    ) -> FetchResult:
        domain = self._domain(url)
        cache_key = f"{url}:{allow_redirects}"

        if use_cache:
            cached = cache.get("http", cache_key)
            if cached:
                return FetchResult(
                    url=cached["url"],
                    status_code=cached["status_code"],
                    headers=cached["headers"],
                    text=cached["text"],
                    elapsed_ms=cached.get("elapsed_ms", 0),
                    from_cache=True,
                    fetched_at=datetime.fromisoformat(cached["fetched_at"]),
                )

        self._wait_if_needed(domain)
        start = time.time()
        response = self._session.get(
            url,
            headers=self._headers(),
            timeout=self.timeout,
            allow_redirects=allow_redirects,
        )
        elapsed_ms = int((time.time() - start) * 1000)
        self._last_request[domain] = time.time()

        result = FetchResult(
            url=str(response.url),
            status_code=response.status_code,
            headers=dict(response.headers),
            text=response.text,
            elapsed_ms=elapsed_ms,
            from_cache=False,
            fetched_at=datetime.now(),
        )

        if use_cache and response.status_code == 200:
            cache.set(
                "http",
                cache_key,
                {
                    "url": result.url,
                    "status_code": result.status_code,
                    "headers": result.headers,
                    "text": result.text,
                    "elapsed_ms": result.elapsed_ms,
                    "fetched_at": result.fetched_at.isoformat(),
                },
                ttl_seconds=ttl_seconds,
            )

        return result

    def head(self, url: str, allow_redirects: bool = True) -> FetchResult:
        domain = self._domain(url)
        self._wait_if_needed(domain)
        start = time.time()
        response = self._session.head(
            url,
            headers=self._headers(),
            timeout=self.timeout,
            allow_redirects=allow_redirects,
        )
        elapsed_ms = int((time.time() - start) * 1000)
        self._last_request[domain] = time.time()
        return FetchResult(
            url=str(response.url),
            status_code=response.status_code,
            headers=dict(response.headers),
            text="",
            elapsed_ms=elapsed_ms,
            from_cache=False,
            fetched_at=datetime.now(),
        )


def create_client() -> PoliteClient:
    return PoliteClient()
