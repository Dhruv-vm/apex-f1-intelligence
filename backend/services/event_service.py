"""APEX — Event, Session, and Results Domain Service."""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from backend.exceptions import EntityNotFoundError
from backend.models import Event, Session as F1Session, RaceResult, Season


class EventService:
    """Provides read operations for canonical F1 entities."""

    @staticmethod
    def get_seasons(db: Session, skip: int = 0, limit: int = 100) -> List[Season]:
        return db.query(Season).order_by(Season.year.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_events(
        db: Session,
        season_year: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Event]:
        query = db.query(Event).options(joinedload(Event.circuit))
        if season_year is not None:
            query = query.filter(Event.season_year == season_year)
        return query.order_by(Event.season_year.desc(), Event.round.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_event_by_id(db: Session, event_id: int) -> Event:
        event = (
            db.query(Event)
            .options(joinedload(Event.circuit), joinedload(Event.sessions))
            .filter(Event.id == event_id)
            .first()
        )
        if not event:
            raise EntityNotFoundError(
                f"Grand Prix Event with ID {event_id} was not found",
                details={"event_id": event_id},
            )
        return event

    @staticmethod
    def get_event_sessions(db: Session, event_id: int) -> List[F1Session]:
        # Ensure event exists first
        EventService.get_event_by_id(db, event_id)
        return (
            db.query(F1Session)
            .filter(F1Session.event_id == event_id)
            .order_by(F1Session.date_start.asc())
            .all()
        )

    @staticmethod
    def get_session_by_id(db: Session, session_id: int) -> F1Session:
        session = db.query(F1Session).filter(F1Session.id == session_id).first()
        if not session:
            raise EntityNotFoundError(
                f"Session with ID {session_id} was not found",
                details={"session_id": session_id},
            )
        return session

    @staticmethod
    def get_event_results(db: Session, event_id: int) -> List[RaceResult]:
        # Ensure event exists first
        EventService.get_event_by_id(db, event_id)
        return (
            db.query(RaceResult)
            .options(joinedload(RaceResult.driver), joinedload(RaceResult.constructor))
            .filter(RaceResult.event_id == event_id)
            .order_by(RaceResult.position_order.asc())
            .all()
        )
