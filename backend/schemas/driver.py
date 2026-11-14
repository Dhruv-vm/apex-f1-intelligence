"""APEX — Driver Schemas."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DriverResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    driver_ref: str
    code: Optional[str] = None
    permanent_number: Optional[int] = None
    first_name: str
    last_name: str
    full_name: str
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    url: Optional[str] = None
