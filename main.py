from src.config.database import init_db, SessionLocal
from src.config.constants import SHEET_CONFIG
import src.models.schemas
from src.services.sync_service import process_sheet
from src.services.maintenance import clean_old_logs

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def main():
    init_db()
    session = SessionLocal()
    
    try:
        for sheet_name, config in SHEET_CONFIG.items():
            process_sheet(sheet_name, config, session)
            
        clean_old_logs(session)
        
    except Exception as e:
        session.rollback()
        logging.exception(f"CRITICAL ERROR during execution: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()