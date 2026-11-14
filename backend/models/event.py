"""APEX — Grand Prix Event Model."""

from sqlalchemy import Column, Integer, String, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import TimestampMixin


class Event(Base, TimestampMixin):
    """Grand Prix race event entity within a Formula 1 season."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    season_year = Column(Integer, ForeignKey("seasons.year", ondelete="CASCADE"), nullable=False, index=True)
    round = Column(Integer, nullable=False)
    event_name = Column(String(128), nullable=False)
    official_name = Column(String(256), nullable=True)
    circuit_id = Column(Integer, ForeignKey("circuits.id", ondelete="RESTRICT"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    time = Column(String(32), nullable=True)
    url = Column(String(256), nullable=True)
    source_provider = Column(String(32), default="jolpica", nullable=False)
    source_id = Column(String(64), nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint("season_year", "round", name="uq_events_season_round"),
    )

    season = relationship("Season", back_populates="events")
    circuit = relationship("Circuit", back_populates="events")
    sessions = relationship("Session", back_populates="event", cascade="all, delete-orphan", order_by="Session.date_start")
    race_results = relationship("RaceResult", back_populates="event", cascade="all, delete-orphan", order_by="RaceResult.position_order")

    def __repr__(self) -> str:
        return f"<Event id={self.id} year={self.season_year} round={self.round} name={self.event_name}>"
