"""APEX — Season Model."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import TimestampMixin


class Season(Base, TimestampMixin):
    """Formula 1 World Championship Season entity."""

    __tablename__ = "seasons"

    year = Column(Integer, primary_key=True, index=True)
    url = Column(String(256), nullable=True)

    events = relationship("Event", back_populates="season", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Season year={self.year}>"
