"""Effective-dated regulation intelligence endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.regulations import (
    RegulationQueryResponse,
    RegulationRecord,
    RegulationRegistry,
    get_regulation_registry,
)

router = APIRouter(prefix="/regulations", tags=["regulations"])


@router.get("", response_model=RegulationQueryResponse)
def query_regulations(
    season: int = Query(2026, description="Championship season"),
    event_date: Optional[str] = Query(None, description="ISO event date YYYY-MM-DD for point-in-time applicability"),
    session_type: Optional[str] = Query(None, description="Optional session filter: FP1, FP2, FP3, QUALIFYING, SPRINT, RACE"),
    category: Optional[str] = Query(None, description="Optional domain filter: POWER_UNIT, AERODYNAMICS, CHASSIS, ENERGY_MANAGEMENT, OVERTAKE_MODE"),
    registry: RegulationRegistry = Depends(get_regulation_registry),
):
    """Query effective-dated technical and sporting regulations applicable to a specific date and session."""
    target_date = event_date or "2026-03-01"  # Default to start of 2026 season
    results = registry.get_applicable_regulations(
        season=season,
        event_date=target_date,
        session_type=session_type,
        category=category,
    )

    return RegulationQueryResponse(
        season=season,
        query_date=target_date,
        session_type=session_type,
        record_count=len(results),
        regulations=results,
    )


@router.get("/{regulation_id}", response_model=RegulationRecord)
def get_regulation_by_id(
    regulation_id: str,
    registry: RegulationRegistry = Depends(get_regulation_registry),
):
    """Retrieve full official details, articles, and provenance for a specific regulation ID."""
    record = registry.get_regulation(regulation_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Regulation '{regulation_id}' not found",
        )
    return record
