"""APEX — Grand Prix Event Schemas."""

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from backend.schemas.circuit import CircuitResponse
from backend.schemas.session import SessionResponse


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    season_year: int
    round: int
    event_name: str
    official_name: Optional[str] = None
    date: date
    time: Optional[str] = None
    url: Optional[str] = None
    circuit: CircuitResponse


class EventDetailResponse(EventResponse):
    sessions: List[SessionResponse] = []
    results_count: int = 0
