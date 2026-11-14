"""APEX — Constructor Model."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import TimestampMixin


class Constructor(Base, TimestampMixin):
    """Formula 1 Team / Constructor entity."""

    __tablename__ = "constructors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    constructor_ref = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    nationality = Column(String(64), nullable=True)
    url = Column(String(256), nullable=True)
    source_provider = Column(String(32), default="jolpica", nullable=False)

    race_results = relationship("RaceResult", back_populates="constructor")

    def __repr__(self) -> str:
        return f"<Constructor id={self.id} ref={self.constructor_ref} name={self.name}>"
