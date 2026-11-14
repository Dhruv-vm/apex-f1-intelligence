"""APEX — Standard Data Provider Interface and Base Implementation."""

import abc
import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, Optional
import httpx
from backend.config import get_settings
from backend.exceptions import ProviderError, ProviderRateLimitError

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseDataProvider(abc.ABC):
    """Abstract base class for all external motorsport data providers."""

    def __init__(self, provider_name: str, base_url: str, cache_dir: str, rate_limit_delay: float):
        self.provider_name = provider_name
        self.base_url = base_url.rstrip("/")
        self.cache_dir = cache_dir
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0
        os.makedirs(self.cache_dir, exist_ok=True)

    def _throttle(self) -> None:
        """Enforces minimum delay between consecutive upstream requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    @staticmethod
    def compute_payload_hash(payload: Any) -> str:
        """Generates a deterministic SHA-256 hash of a payload dictionary or string."""
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _get_cache_filepath(self, cache_key: str) -> str:
        safe_key = "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in cache_key)
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def _read_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        path = self._get_cache_filepath(cache_key)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    logger.debug(f"[{self.provider_name}] Cache HIT: {cache_key}")
                    return json.load(f)
            except Exception as e:
                logger.warning(f"[{self.provider_name}] Error reading cache file {path}: {e}")
        return None

    def _write_to_cache(self, cache_key: str, data: Any) -> None:
        path = self._get_cache_filepath(cache_key)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug(f"[{self.provider_name}] Cached response: {cache_key}")
        except Exception as e:
            logger.warning(f"[{self.provider_name}] Failed to write cache {path}: {e}")

    def fetch_json(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Fetches JSON data with local disk caching, retry backoff, and rate limiting."""
        if cache_key and not force_refresh:
            cached = self._read_from_cache(cache_key)
            if cached is not None:
                return cached

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        retries = settings.MAX_RETRIES
        backoff = 1.0

        for attempt in range(1, retries + 1):
            self._throttle()
            try:
                logger.info(f"[{self.provider_name}] Requesting {url} (Attempt {attempt}/{retries})")
                with httpx.Client(timeout=settings.TIMEOUT_SECONDS) as client:
                    resp = client.get(url, params=params)

                if resp.status_code == 429:
                    if attempt < retries:
                        time.sleep(backoff * 2)
                        continue
                    raise ProviderRateLimitError(
                        f"[{self.provider_name}] Upstream rate limit exceeded (HTTP 429)",
                        details={"url": url, "attempt": attempt},
                    )

                if resp.status_code != 200:
                    raise ProviderError(
                        f"[{self.provider_name}] Received HTTP {resp.status_code} from {url}",
                        details={"status_code": resp.status_code, "response_text": resp.text[:200]},
                    )

                data = resp.json()
                if cache_key:
                    self._write_to_cache(cache_key, data)
                return data

            except (httpx.RequestError, httpx.TimeoutException) as exc:
                logger.warning(f"[{self.provider_name}] Network error on attempt {attempt}: {exc}")
                if attempt == retries:
                    raise ProviderError(
                        f"[{self.provider_name}] Connection failed after {retries} attempts: {exc}",
                        details={"url": url, "error": str(exc)},
                    )
                time.sleep(backoff)
                backoff *= 1.5

        raise ProviderError(f"[{self.provider_name}] Request failed unexpectedly for {url}")
