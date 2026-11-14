"""APEX — Grand Prix Events Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from backend.api.deps import get_db
from backend.schemas.event import EventResponse, EventDetailResponse
from backend.schemas.session import SessionResponse
from backend.schemas.race_result import RaceResultResponse
from backend.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=List[EventResponse], status_code=status.HTTP_200_OK)
def list_events(
    season: Optional[int] = Query(default=None, description="Filter by championship season year"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[EventResponse]:
    """Retrieves Grand Prix events, optionally filtered by season."""
    return EventService.get_events(db, season_year=season, skip=skip, limit=limit)


@router.get("/{event_id}", response_model=EventDetailResponse, status_code=status.HTTP_200_OK)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
) -> EventDetailResponse:
    """Retrieves full details for a Grand Prix event including sessions and results count."""
    event = EventService.get_event_by_id(db, event_id=event_id)
    return EventDetailResponse(
        id=event.id,
        season_year=event.season_year,
        round=event.round,
        event_name=event.event_name,
        official_name=event.official_name,
        date=event.date,
        time=event.time,
        url=event.url,
        circuit=event.circuit,
        sessions=event.sessions,
        results_count=len(event.race_results),
    )


@router.get("/{event_id}/sessions", response_model=List[SessionResponse], status_code=status.HTTP_200_OK)
def get_event_sessions(
    event_id: int,
    db: Session = Depends(get_db),
) -> List[SessionResponse]:
    """Retrieves scheduled or completed sessions for a Grand Prix event."""
    return EventService.get_event_sessions(db, event_id=event_id)


@router.get("/{event_id}/results", response_model=List[RaceResultResponse], status_code=status.HTTP_200_OK)
def get_event_results(
    event_id: int,
    db: Session = Depends(get_db),
) -> List[RaceResultResponse]:
    """Retrieves classified race results for a Grand Prix event ordered by finishing rank."""
    return EventService.get_event_results(db, event_id=event_id)
