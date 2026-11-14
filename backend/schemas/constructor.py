"""APEX — Constructor Schemas."""

from typing import Optional
from pydantic import BaseModel, ConfigDict


class ConstructorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    constructor_ref: str
    name: str
    nationality: Optional[str] = None
    url: Optional[str] = None
