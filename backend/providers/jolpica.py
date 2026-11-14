"""APEX — Jolpica / Ergast Data Provider Adapter."""

import glob
import json
import logging
import os
from typing import Any, Dict, List, Optional
from backend.config import get_settings
from backend.exceptions import ProviderError
from backend.providers.base import BaseDataProvider

logger = logging.getLogger(__name__)
settings = get_settings()


class JolpicaProvider(BaseDataProvider):
    """Adapter for the Ergast/Jolpica REST API providing historical sporting records."""

    def __init__(self):
        super().__init__(
            provider_name="jolpica",
            base_url=settings.JOLPICA_BASE_URL,
            cache_dir=settings.JOLPICA_CACHE_DIR,
            rate_limit_delay=settings.JOLPICA_RATE_LIMIT_DELAY,
        )

    def _find_in_existing_season_cache(self, season: int, round_num: int) -> Optional[Dict[str, Any]]:
        """Searches existing cached results JSON files under data/raw/jolpica/results/{season}/."""
        search_dirs = [
            os.path.join(self.cache_dir, "results", str(season)),
            os.path.join(self.cache_dir, "results"),
        ]
        for sdir in search_dirs:
            if not os.path.exists(sdir):
                continue
            for filepath in glob.glob(os.path.join(sdir, "*.json")):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
                    for r in races:
                        if str(r.get("season")) == str(season) and str(r.get("round")) == str(round_num):
                            logger.info(f"[jolpica] Found season {season} round {round_num} in local raw file {filepath}")
                            return r
                except Exception:
                    continue
        return None

    def get_seasons(self, limit: int = 100, offset: int = 0, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Retrieves historical Formula 1 seasons list."""
        cache_key = f"seasons_limit_{limit}_offset_{offset}"
        data = self.fetch_json(
            endpoint="seasons.json",
            params={"limit": limit, "offset": offset},
            cache_key=cache_key,
            force_refresh=force_refresh,
        )
        season_table = data.get("MRData", {}).get("SeasonTable", {})
        return season_table.get("Seasons", [])

    def get_race_results(self, season: int, round_num: int, force_refresh: bool = False) -> Dict[str, Any]:
        """Retrieves event metadata, circuit details, and finishing results for a specific round."""
        cache_key = f"results_{season}_round_{round_num}"

        # 1. Check existing dedicated cache
        if not force_refresh:
            cached = self._read_from_cache(cache_key)
            if cached:
                return cached

            # 2. Check existing multi-race batch raw cache
            existing_race = self._find_in_existing_season_cache(season, round_num)
            if existing_race:
                self._write_to_cache(cache_key, existing_race)
                return existing_race

        # 3. Fetch from remote Jolpica API
        endpoint = f"{season}/{round_num}/results.json"
        data = self.fetch_json(
            endpoint=endpoint,
            params={"limit": 100},
            cache_key=f"api_{cache_key}",
            force_refresh=force_refresh,
        )

        races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        if not races:
            raise ProviderError(
                f"[jolpica] No race results found for season {season} round {round_num}",
                details={"season": season, "round": round_num},
            )

        race = races[0]
        self._write_to_cache(cache_key, race)
        return race
