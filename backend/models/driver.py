"""APEX — Driver Model."""

from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import TimestampMixin


class Driver(Base, TimestampMixin):
    """Formula 1 Driver entity."""

    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_ref = Column(String(64), unique=True, nullable=False, index=True)
    code = Column(String(8), nullable=True, index=True)
    permanent_number = Column(Integer, nullable=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    nationality = Column(String(64), nullable=True)
    url = Column(String(256), nullable=True)
    source_provider = Column(String(32), default="jolpica", nullable=False)

    race_results = relationship("RaceResult", back_populates="driver")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Driver id={self.id} ref={self.driver_ref} code={self.code}>"
