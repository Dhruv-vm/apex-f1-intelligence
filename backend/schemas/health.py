"""APEX — Health & Readiness Schemas."""

from typing import Any, Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="Service status", json_schema_extra={"example": "healthy"})
    environment: str = Field(description="Environment name", json_schema_extra={"example": "development"})
    version: str = Field(description="API version", json_schema_extra={"example": "0.1.0"})
    database: str = Field(description="Database connectivity", json_schema_extra={"example": "connected"})


class ReadinessResponse(BaseModel):
    status: str = Field(description="Readiness status", json_schema_extra={"example": "ready"})
    database_connected: bool = Field(description="PostgreSQL connectivity flag", json_schema_extra={"example": True})
    details: Dict[str, Any] = Field(default_factory=dict)
