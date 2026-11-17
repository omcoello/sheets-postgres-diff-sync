from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid
from sqlalchemy.orm import declarative_base
from datetime import datetime, UTC

Base = declarative_base()

class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sheet_name = Column(String, index=True, nullable=False)
    action = Column(String, nullable=False)
    record_key = Column(String, nullable=False)
    changes = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC), index=True)
