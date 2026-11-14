"""APEX — Ingestion Log Model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.database import Base


class IngestionLog(Base):
    """Tracks provider ingestion provenance, payload hash, and outcome for idempotency."""

    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(32), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False)
    identifier = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False)  # "SUCCESS", "FAILED", "PARTIAL"
    records_ingested = Column(Integer, default=0, nullable=False)
    payload_hash = Column(String(64), nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<IngestionLog id={self.id} provider={self.provider} id={self.identifier} status={self.status}>"
