from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from src.config.constants import DAYS_TO_KEEP_LOGS
from src.models.schemas import SyncLog

def clean_old_logs(session: Session, days: int = DAYS_TO_KEEP_LOGS):
    """Deletes logs older than the specified number of days."""
    cutoff_date = datetime.now(UTC) - timedelta(days=int(days))
    deleted_count = session.query(SyncLog).filter(SyncLog.created_at < cutoff_date).delete()
    session.commit()
    print(f"Maintenance: Cleaned {deleted_count} logs older than {days} days.")