import os
from dotenv import load_dotenv

load_dotenv()

# Database Config
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "delegate_processing")

# Sheet Config
SHEET_ID = os.getenv("SHEET_ID","")
DAYS_TO_KEEP_LOGS = int(os.getenv("DAYS_TO_KEEP_LOGS", 15))
SHEET_CONFIG = {
    "ASIGN": {
        "gid": "1486651786", 
        "pk_columns": ["CustomOrder", "Código"],
        "header_row": 1
    },
    "ASIGN_CAMPUS3": {
        "gid": 1995429093,
        "pk_columns": ["CustomOrder", "Código"],
        "header_row": 0
    },
    "FP092": {
        "gid": 1541466562,
        "pk_columns": ["Área"],
        "header_row": 0
    },
    "COORDINADORES": {
        "gid": 482798911,
        "pk_columns": ["Código"],
        "header_row": 0
    },
    "EXCEPCIONES": {
        "gid": 1072759729,
        "pk_columns": ["Entidad", "Persona"],
        "header_row": 0
    },
    "ProfesoresCV": {
        "gid": 669197974,
        "pk_columns": ["email"],
        "header_row": 0
    },
}
