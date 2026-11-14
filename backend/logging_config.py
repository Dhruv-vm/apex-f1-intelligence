"""APEX — Structured Logging Configuration."""

import logging
import sys
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """Formats log records with timestamp, level, module, and message."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Human-readable structured console log
        return f"[{payload['timestamp']}] [{payload['level']}] [{payload['logger']}]: {payload['message']}"


def setup_logging(level_name: str = "INFO") -> None:
    """Configure root logger with unified formatting."""
    log_level = getattr(logging, level_name.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if re-called
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
        root_logger.addHandler(handler)

    # Reduce noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
