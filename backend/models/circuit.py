"""APEX — Circuit Model."""

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import TimestampMixin


class Circuit(Base, TimestampMixin):
    """Grand Prix Circuit / Track entity."""

    __tablename__ = "circuits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    circuit_ref = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    location = Column(String(128), nullable=True)
    country = Column(String(64), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    url = Column(String(256), nullable=True)
    source_provider = Column(String(32), default="jolpica", nullable=False)

    events = relationship("Event", back_populates="circuit")

    def __repr__(self) -> str:
        return f"<Circuit id={self.id} ref={self.circuit_ref} name={self.name}>"
