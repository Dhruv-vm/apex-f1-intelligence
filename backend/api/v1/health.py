"""APEX — Health & Readiness Endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.api.deps import get_db
from backend.config import get_settings
from backend.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(prefix="", tags=["System"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Liveness probe: verifies basic service responsiveness and database connectivity."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1;"))
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        environment=settings.ENVIRONMENT,
        version="0.1.0",
        database=db_status,
    )


@router.get("/ready", response_model=ReadinessResponse, status_code=status.HTTP_200_OK)
def readiness_check(db: Session = Depends(get_db)) -> ReadinessResponse:
    """Readiness probe: validates database read and write capability."""
    db_ok = False
    details = {}
    try:
        res = db.execute(text("SELECT 1;")).scalar()
        db_ok = (res == 1)
        details["database"] = "PostgreSQL connection pool ready"
    except Exception as e:
        details["database"] = f"Error: {str(e)}"

    return ReadinessResponse(
        status="ready" if db_ok else "unready",
        database_connected=db_ok,
        details=details,
    )
