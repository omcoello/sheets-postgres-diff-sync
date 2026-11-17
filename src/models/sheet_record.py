from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, UTC

Base = declarative_base()

class SheetRecord(Base):
    __tablename__ = "sheet_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sheet_name = Column(String, index=True, nullable=False)
    record_key = Column(String, index=True, nullable=False)
    row_data = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))