"""APEX — FastF1 Optional Provider Adapter."""

import logging
import os
from typing import Any, Dict, Optional
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FastF1Provider:
    """Optional adapter for FastF1 python package.

    Safely degrades if fastf1 is not installed or when sessions are auth-gated.
    """

    def __init__(self):
        self.provider_name = "fastf1"
        self.cache_dir = settings.FASTF1_CACHE_DIR
        self._is_available = False
        try:
            import fastf1  # type: ignore
            os.makedirs(self.cache_dir, exist_ok=True)
            fastf1.Cache.enable_cache(self.cache_dir)
            self._is_available = True
            logger.info("[fastf1] FastF1 initialized with cache dir: %s", self.cache_dir)
        except ImportError:
            logger.info("[fastf1] FastF1 not installed. Operating in degraded mode.")
        except Exception as e:
            logger.warning("[fastf1] FastF1 cache initialization error: %s", e)

    @property
    def is_available(self) -> bool:
        return self._is_available

    def get_session(self, year: int, race_round: int, session_type: str = "R") -> Optional[Dict[str, Any]]:
        """Safely attempts to load a session without breaking callers if unauthorized or failed."""
        if not self._is_available:
            return None
        try:
            import fastf1
            session = fastf1.get_session(year, race_round, session_type)
            session.load(telemetry=False, weather=False, messages=False)
            return {
                "name": session.name,
                "date": str(session.date),
                "total_laps": len(session.laps) if hasattr(session, "laps") else 0,
            }
        except Exception as e:
            logger.warning("[fastf1] Could not load session %s-%s (%s): %s", year, race_round, session_type, e)
            return None
