"""APEX — FastAPI Dependencies."""

from typing import Generator
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from backend.config import Settings, get_settings
from backend.database import SessionLocal
from backend.exceptions import AuthenticationError


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a thread-local database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_admin_key(
    x_admin_key: str = Header(None, alias="X-Admin-Key"),
    settings: Settings = Depends(get_settings),
) -> str:
    """Verifies secret key for protected administrative ingestion operations."""
    if not x_admin_key or x_admin_key != settings.ADMIN_API_KEY:
        raise AuthenticationError(
            "Missing or invalid administrative API key in X-Admin-Key header",
            details={"required_header": "X-Admin-Key"},
        )
    return x_admin_key
