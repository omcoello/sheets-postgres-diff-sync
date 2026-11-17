import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.config.database import Base

class SheetRecord(Base):
    __tablename__ = "sheet_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sheet_name = Column(String, index=True, nullable=False)
    record_key = Column(String, index=True, nullable=False)
    row_data = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sheet_name = Column(String, index=True, nullable=False)
    action = Column(String, nullable=False)
    record_key = Column(String, nullable=False)
    changes = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC), index=True)