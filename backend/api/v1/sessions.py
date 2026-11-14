"""APEX — Sessions Endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.api.deps import get_db
from backend.schemas.session import SessionResponse
from backend.services.event_service import EventService

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/{session_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Retrieves metadata for a specific session by its internal surrogate ID."""
    return EventService.get_session_by_id(db, session_id=session_id)
