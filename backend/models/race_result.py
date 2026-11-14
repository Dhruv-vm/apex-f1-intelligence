"""APEX — Race Result Model."""

from sqlalchemy import Column, Integer, BigInteger, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import TimestampMixin


class RaceResult(Base, TimestampMixin):
    """Grand Prix Race Result record for an individual driver."""

    __tablename__ = "race_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="RESTRICT"), nullable=False, index=True)
    constructor_id = Column(Integer, ForeignKey("constructors.id", ondelete="RESTRICT"), nullable=False, index=True)

    number = Column(Integer, nullable=True)
    grid_position = Column(Integer, nullable=False)
    position = Column(Integer, nullable=True)  # Nullable for unclassified / DNF
    position_text = Column(String(16), nullable=False)  # "1", "2", "R", "D", "W"
    position_order = Column(Integer, nullable=False)
    points = Column(Float, nullable=False, default=0.0)
    laps = Column(Integer, nullable=False, default=0)
    status = Column(String(64), nullable=False)  # "Finished", "+1 Lap", "Engine", "Collision"

    time_millis = Column(BigInteger, nullable=True)
    time_string = Column(String(32), nullable=True)

    fastest_lap_rank = Column(Integer, nullable=True)
    fastest_lap_lap = Column(Integer, nullable=True)
    fastest_lap_time = Column(String(32), nullable=True)
    fastest_lap_speed = Column(Float, nullable=True)

    source_provider = Column(String(32), default="jolpica", nullable=False)

    __table_args__ = (
        UniqueConstraint("event_id", "driver_id", name="uq_results_event_driver"),
    )

    event = relationship("Event", back_populates="race_results")
    driver = relationship("Driver", back_populates="race_results")
    constructor = relationship("Constructor", back_populates="race_results")

    def __repr__(self) -> str:
        return f"<RaceResult event_id={self.event_id} driver_id={self.driver_id} pos={self.position_text}>"
