"""APEX — Session Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    session_type: str
    session_name: str
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    source_provider: str
    source_session_key: Optional[int] = None
