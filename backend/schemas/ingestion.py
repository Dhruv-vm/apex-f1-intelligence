"""APEX — Ingestion Request & Response Schemas."""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class IngestionRequest(BaseModel):
    season: int = Field(description="Championship season year", json_schema_extra={"example": 2024})
    round: int = Field(description="Grand Prix round number", json_schema_extra={"example": 24})
    force_refresh: bool = Field(default=False, description="Bypass local raw cache if True")


class IngestionResponse(BaseModel):
    status: str = Field(description="Ingestion result status", json_schema_extra={"example": "SUCCESS"})
    event_id: int
    season: int
    round: int
    event_name: str
    records_ingested: Dict[str, int]
    message: str
    error: Optional[str] = None
