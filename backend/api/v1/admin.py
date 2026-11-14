"""APEX — Administrative Ingestion Endpoints."""

import re
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from backend.api.deps import get_db, verify_admin_key
from backend.exceptions import IngestionError
from backend.models import Event
from backend.schemas.ingestion import IngestionResponse
from backend.services.ingestion_service import IngestionService

router = APIRouter(prefix="/admin/ingestion", tags=["Admin Ingestion"])


@router.post(
    "/events/{event_id}",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_admin_key)],
)
def trigger_event_ingestion(
    event_id: str,
    season: Optional[int] = Query(default=None, description="Explicit season year if event_id is round"),
    round: Optional[int] = Query(default=None, description="Explicit round number"),
    force_refresh: bool = Query(default=False, description="Bypass local raw cache if True"),
    db: Session = Depends(get_db),
) -> IngestionResponse:
    """Triggers idempotent ingestion for a Grand Prix event.

    Requires valid 'X-Admin-Key' header. Accepts event_id as:
    - 'YYYY_RR' format (e.g. '2024_24')
    - Existing integer database Event ID
    - Or explicit 'season' and 'round' query parameters.
    """
    season_val = season
    round_val = round

    # Check if event_id is 'YYYY_RR'
    match = re.match(r"^(\d{4})_(\d{1,2})$", event_id)
    if match:
        season_val = int(match.group(1))
        round_val = int(match.group(2))
    elif event_id.isdigit():
        numeric_id = int(event_id)
        # Check if it matches an existing event
        existing_event = db.query(Event).filter(Event.id == numeric_id).first()
        if existing_event:
            season_val = existing_event.season_year
            round_val = existing_event.round
        elif season_val is None:
            # Fall back to assuming round number with provided season
            round_val = numeric_id

    if season_val is None or round_val is None:
        raise IngestionError(
            f"Could not determine season and round from event_id '{event_id}'. "
            f"Provide 'YYYY_RR' format or pass 'season' and 'round' query parameters.",
            details={"event_id": event_id, "season": season, "round": round},
        )

    service = IngestionService()
    result = service.ingest_event(
        db=db,
        season_year=season_val,
        round_num=round_val,
        force_refresh=force_refresh,
    )

    return IngestionResponse(
        status=result["status"],
        event_id=result["event_id"],
        season=result["season"],
        round=result["round"],
        event_name=result["event_name"],
        records_ingested=result["records_ingested"],
        message=result["message"],
    )
