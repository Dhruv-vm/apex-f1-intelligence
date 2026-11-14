"""APEX — Seasons Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from backend.api.deps import get_db
from backend.schemas.season import SeasonResponse
from backend.services.event_service import EventService

router = APIRouter(prefix="/seasons", tags=["Seasons"])


@router.get("", response_model=List[SeasonResponse], status_code=status.HTTP_200_OK)
def list_seasons(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[SeasonResponse]:
    """Retrieves all persisted championship seasons sorted chronologically descending."""
    return EventService.get_seasons(db, skip=skip, limit=limit)
