import logging
import pandas as pd
from dataclasses import dataclass, field
from typing import Any
from sqlalchemy.orm import Session
from src.config.constants import SHEET_ID
from src.models.schemas import SheetRecord, SyncLog
from src.utils.sheet_helpers import (
    generate_record_key,
    get_google_sheet_csv_url,
    get_row_differences,
)

logger = logging.getLogger(__name__)

@dataclass
class SyncSummary:
    """Holds the categorized results of a sheet synchronization run."""
    inserts: list[dict[str, Any]] = field(default_factory=list)
    updates: list[dict[str, Any]] = field(default_factory=list)
    deletes: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.inserts or self.updates or self.deletes)


def process_sheet(sheet_name: str, config: dict[str, Any], session: Session) -> SyncSummary | None:
    """
    Orchestrates the download, diffing, and database synchronization for a single sheet.
    """
    logger.info("--- Processing Sheet: %s ---", sheet_name.upper())
    
    df = _fetch_and_clean_sheet(sheet_name, config)
    if df is None:
        return None

    df = _handle_duplicates(session, sheet_name, df, config["pk_columns"])
    
    db_state = _get_active_db_records(session, sheet_name)
    summary = _apply_diff_operations(
        session=session,
        sheet_name=sheet_name,
        df=df,
        pk_columns=config["pk_columns"],
        db_state=db_state,
    )

    if _commit_changes(session, sheet_name):
        _emit_sync_events(sheet_name, summary)
        return summary

    return None


def _fetch_and_clean_sheet(sheet_name: str, config: dict[str, Any]) -> pd.DataFrame | None:
    """Downloads a Google Sheet as a CSV and normalizes missing values to None."""
    url = get_google_sheet_csv_url(SHEET_ID, config["gid"])
    try:
        df = pd.read_csv(url, header=config.get("header_row", 0))
    except Exception:
        logger.exception("Error downloading sheet '%s'", sheet_name)
        return None

    # Replace NaN/NaT with None for JSONB compatibility
    return df.astype(object).where(pd.notna(df), None)


def _get_active_db_records(session: Session, sheet_name: str) -> dict[str, SheetRecord]:
    """Fetches active database records mapped by their unique record_key."""
    active_records = (
        session.query(SheetRecord)
        .filter(
            SheetRecord.sheet_name == sheet_name,
            SheetRecord.is_active.is_(True),
        )
        .all()
    )
    return {record.record_key: record for record in active_records}


def _apply_diff_operations(
    session: Session,
    sheet_name: str,
    df: pd.DataFrame,
    pk_columns: list[str],
    db_state: dict[str, SheetRecord],
) -> SyncSummary:
    """Compares incoming sheet rows against DB state and stages inserts, updates, and soft-deletes."""
    summary = SyncSummary()
    processed_keys: set[str] = set()

    for row_dict in df.to_dict(orient="records"):
        record_key = generate_record_key(row_dict, pk_columns)
        processed_keys.add(record_key)

        if record_key not in db_state:
            _stage_insert(session, sheet_name, record_key, row_dict, summary)
        else:
            _stage_update_if_changed(
                session, sheet_name, record_key, row_dict, db_state[record_key], summary
            )

    missing_keys = set(db_state.keys()) - processed_keys
    for missing_key in missing_keys:
        _stage_soft_delete(session, sheet_name, missing_key, db_state[missing_key], summary)

    return summary


def _stage_insert(
    session: Session,
    sheet_name: str,
    record_key: str,
    row_data: dict[str, Any],
    summary: SyncSummary,
) -> None:
    session.add(
        SheetRecord(
            sheet_name=sheet_name,
            record_key=record_key,
            row_data=row_data,
            is_active=True,
        )
    )
    session.add(
        SyncLog(
            sheet_name=sheet_name,
            action="INSERT",
            record_key=record_key,
            changes={"new_data": row_data},
        )
    )
    summary.inserts.append(row_data)


def _stage_update_if_changed(
    session: Session,
    sheet_name: str,
    record_key: str,
    row_data: dict[str, Any],
    db_record: SheetRecord,
    summary: SyncSummary,
) -> None:
    differences = get_row_differences(db_record.row_data, row_data)
    if not differences:
        return

    db_record.row_data = row_data
    session.add(
        SyncLog(
            sheet_name=sheet_name,
            action="UPDATE",
            record_key=record_key,
            changes=differences,
        )
    )
    summary.updates.append({"record_key": record_key, "changes": differences})


def _stage_soft_delete(
    session: Session,
    sheet_name: str,
    record_key: str,
    db_record: SheetRecord,
    summary: SyncSummary,
) -> None:
    db_record.is_active = False
    session.add(
        SyncLog(
            sheet_name=sheet_name,
            action="DELETE",
            record_key=record_key,
            changes={"deleted_data": db_record.row_data},
        )
    )
    summary.deletes.append({"record_key": record_key, "deleted_data": db_record.row_data})


def _commit_changes(session: Session, sheet_name: str) -> bool:
    try:
        session.commit()
        return True
    except Exception:
        session.rollback()
        logger.exception(
            "Error saving '%s' to DB. Events aborted to prevent inconsistency.", sheet_name
        )
        return False


def _emit_sync_events(sheet_name: str, summary: SyncSummary) -> None:
    logger.info(
        "Result for '%s': %d Inserts, %d Updates, %d Deletes.",
        sheet_name,
        len(summary.inserts),
        len(summary.updates),
        len(summary.deletes),
    )

    if summary.inserts:
        logger.info("[*] Ready to emit INSERT event with %d records.", len(summary.inserts))
    if summary.updates:
        logger.info("[*] Ready to emit UPDATE event with %d records.", len(summary.updates))
    if summary.deletes:
        logger.info("[*] Ready to emit DELETE event with %d records.", len(summary.deletes))
        
def _handle_duplicates(
    session: Session, sheet_name: str, df: pd.DataFrame, pk_columns: list[str]
) -> pd.DataFrame:
    """
    Filters out duplicate rows based on the primary key and logs warnings to SyncLog.
    """
    if df.empty:
        return df

    record_keys = pd.Series(
        [generate_record_key(row, pk_columns) for row in df.to_dict(orient="records")],
        index=df.index,
    )
    duplicated_mask = record_keys.duplicated(keep="first")

    if not duplicated_mask.any():
        return df

    duplicated_keys = record_keys[duplicated_mask].unique().tolist()
    logger.warning(
        "Duplicate keys detected in '%s': %s. Ignoring duplicates to protect DB integrity.",
        sheet_name,
        duplicated_keys,
    )

    for dup_key in duplicated_keys:
        session.add(
            SyncLog(
                sheet_name=sheet_name,
                action="DUPLICATE_WARNING",
                record_key=dup_key,
                changes={
                    "warning": "Duplicate primary key found in Google Sheets. Only the first occurrence was processed."
                },
            )
        )

    return df.loc[~duplicated_mask].copy()