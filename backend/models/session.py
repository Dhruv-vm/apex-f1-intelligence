"""APEX — Session Model."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import TimestampMixin


class Session(Base, TimestampMixin):
    """Specific on-track session (FP1, FP2, FP3, Qualifying, Sprint, Race)."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    session_type = Column(String(32), nullable=False)  # "fp1", "fp2", "fp3", "qualifying", "sprint", "race"
    session_name = Column(String(64), nullable=False)  # "Practice 1", "Qualifying", "Race"
    date_start = Column(DateTime(timezone=True), nullable=True)
    date_end = Column(DateTime(timezone=True), nullable=True)
    source_provider = Column(String(32), default="openf1", nullable=False)
    source_session_key = Column(Integer, nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint("event_id", "session_type", name="uq_sessions_event_type"),
    )

    event = relationship("Event", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session id={self.id} event_id={self.event_id} type={self.session_type} key={self.source_session_key}>"
