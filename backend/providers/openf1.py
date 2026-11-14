"""APEX — OpenF1 Community Data Provider Adapter."""

import json
import logging
import os
from typing import Any, Dict, List, Optional
from backend.config import get_settings
from backend.providers.base import BaseDataProvider

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenF1Provider(BaseDataProvider):
    """Adapter for the OpenF1 Community REST API providing session and telemetry data."""

    def __init__(self):
        super().__init__(
            provider_name="openf1",
            base_url=settings.OPENF1_BASE_URL,
            cache_dir=settings.OPENF1_CACHE_DIR,
            rate_limit_delay=settings.OPENF1_RATE_LIMIT_DELAY,
        )

    def _find_in_sessions_dir(self, year: int, country_name: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Checks if pre-cached session files exist under data/raw/openf1/sessions/."""
        sessions_dir = os.path.join(self.cache_dir, "sessions")
        if not os.path.exists(sessions_dir):
            return None

        # Check for matching filename like 2024_abu_dhabi.json
        for fname in os.listdir(sessions_dir):
            if fname.endswith(".json") and str(year) in fname:
                if country_name and "emirates" in country_name.lower() and "abu_dhabi" in fname.lower():
                    try:
                        with open(os.path.join(sessions_dir, fname), "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                return data
                    except Exception as e:
                        logger.warning(f"[openf1] Error reading session cache {fname}: {e}")
        return None

    def get_sessions(
        self,
        year: int,
        country_name: Optional[str] = None,
        circuit_short_name: Optional[str] = None,
        force_refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """Retrieves sessions for a given year and circuit/country."""
        cache_key = f"sessions_{year}_{country_name or ''}_{circuit_short_name or ''}"

        if not force_refresh:
            cached = self._read_from_cache(cache_key)
            if cached is not None and isinstance(cached, list):
                return cached

            pre_cached = self._find_in_sessions_dir(year, country_name)
            if pre_cached:
                self._write_to_cache(cache_key, pre_cached)
                return pre_cached

        params: Dict[str, Any] = {"year": year}
        if country_name:
            params["country_name"] = country_name
        if circuit_short_name:
            params["circuit_short_name"] = circuit_short_name

        data = self.fetch_json(
            endpoint="sessions",
            params=params,
            cache_key=cache_key,
            force_refresh=force_refresh,
        )
        return data if isinstance(data, list) else []

    def get_drivers(self, session_key: int, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Retrieves driver entries for a specific OpenF1 session."""
        cache_key = f"drivers_session_{session_key}"

        # Check pre-cached drivers dir
        driver_cache_file = os.path.join(self.cache_dir, "drivers", f"{session_key}.json")
        if not force_refresh and os.path.exists(driver_cache_file):
            try:
                with open(driver_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception:
                pass

        if not force_refresh:
            cached = self._read_from_cache(cache_key)
            if cached is not None and isinstance(cached, list):
                return cached

        data = self.fetch_json(
            endpoint="drivers",
            params={"session_key": session_key},
            cache_key=cache_key,
            force_refresh=force_refresh,
        )
        return data if isinstance(data, list) else []
