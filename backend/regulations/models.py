"""Data models for effective-dated 2026 regulation intelligence registry."""
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class RegulationRecord(BaseModel):
    """Canonical representation of an effective-dated technical/sporting regulation."""
    regulation_id: str = Field(..., description="Unique alphanumeric identifier (e.g. REG-2026-PU-001)")
    season: int = Field(..., description="Championship season applicable")
    category: str = Field(..., description="Regulatory domain: POWER_UNIT, AERODYNAMICS, CHASSIS, ENERGY, OVERTAKE")
    parameter_name: str = Field(..., description="Specific parameter governed")
    parameter_value: str = Field(..., description="Prescribed numerical or qualitative parameter value")
    units: Optional[str] = Field(None, description="Physical units of measure (kW, kg, mm, MJ)")
    description: str = Field(..., description="Concise technical summary of the rule")
    official_source: str = Field(..., description="Official FIA document title")
    source_url: Optional[str] = Field(None, description="Direct URL to FIA published bulletin/regulations")
    document_issue: str = Field(..., description="Document version/issue (e.g. Issue 6, WMSC Amendment)")
    relevant_article: str = Field(..., description="Section / Article reference (e.g. Article 5.4.1)")
    publication_date: str = Field(..., description="ISO publication date YYYY-MM-DD")
    approval_date: str = Field(..., description="ISO WMSC approval date YYYY-MM-DD")
    effective_from: str = Field(..., description="Earliest ISO event date rule applies YYYY-MM-DD")
    effective_until: Optional[str] = Field(None, description="Latest ISO date rule applies or None if active")
    session_applicability: List[str] = Field(
        default_factory=lambda: ["FP1", "FP2", "FP3", "QUALIFYING", "SPRINT", "RACE"],
        description="Sessions where this regulation is strictly enforced"
    )
    approval_status: str = Field(..., description="APPROVED, AMENDED, SUPERSEDED, or PROPOSED")
    provenance_notes: str = Field(..., description="Audit traceability and verification notes")


class RegulationQueryResponse(BaseModel):
    """Response envelope for regulation queries."""
    season: int
    query_date: Optional[str] = None
    session_type: Optional[str] = None
    record_count: int
    regulations: List[RegulationRecord]
