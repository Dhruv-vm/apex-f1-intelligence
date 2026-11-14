"""APEX — Season Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SeasonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    url: Optional[str] = None
    created_at: datetime
