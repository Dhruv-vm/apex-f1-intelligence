"""APEX — Circuit Schemas."""

from typing import Optional
from pydantic import BaseModel, ConfigDict


class CircuitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    circuit_ref: str
    name: str
    location: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    url: Optional[str] = None
