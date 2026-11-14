"""APEX — Race Result Schemas."""

from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.schemas.driver import DriverResponse
from backend.schemas.constructor import ConstructorResponse


class RaceResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    driver: DriverResponse
    constructor: ConstructorResponse
    number: Optional[int] = None
    grid_position: int
    position: Optional[int] = None
    position_text: str
    position_order: int
    points: float
    laps: int
    status: str
    time_millis: Optional[int] = None
    time_string: Optional[str] = None
    fastest_lap_rank: Optional[int] = None
    fastest_lap_lap: Optional[int] = None
    fastest_lap_time: Optional[str] = None
    fastest_lap_speed: Optional[float] = None
