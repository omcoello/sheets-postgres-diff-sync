# 📊 Google Sheets to PostgreSQL Sync & Diff Engine

A generic, schema-agnostic Change Data Capture (CDC) synchronization service built in Python. It extracts data from multi-tab Google Sheets, detects row-level additions, modifications, and deletions, persists state in PostgreSQL using flexible `JSONB` payloads, and prepares batch events for message brokers (e.g., RabbitMQ).

## 🚀 Key Features

* **Schema-Agnostic Persistence:** Uses PostgreSQL `JSONB` to store row payloads, allowing columns in Google Sheets to be reordered, added, or removed without breaking database schemas or requiring migrations.
* **Generic Diff Engine:** Accurately identifies `INSERT`, `UPDATE` (column-by-column diffing), and `DELETE` (soft-deletes) across any sheet structure via configurable single or composite primary keys.
* **Human-Error Resilience:** Built-in deduplication quarantines duplicate primary keys before database staging, logging warnings without halting execution or corrupting state.
* **Audit & Retention Policies:** Tracks granular before/after changes in a centralized `sync_logs` table with automated log rotation (default: 15 days).
* **Event-Driven Ready:** Accumulates categorized changes per sheet and safely stages event emission strictly after database transaction commits.

---

## 🏗️ Project Architecture

```text
proyecto/
├── .env
├── main.py                  # Application entry point & orchestrator
└── src/
    ├── __init__.py
    ├── config/
    │   ├── __init__.py
    │   ├── constants.py     # Sheet mappings, GIDs, PK definitions, and retention settings
    │   └── database.py      # SQLAlchemy engine, session factory, and Base declaration
    ├── models/
    │   ├── __init__.py
    │   └── schemas.py       # PostgreSQL ORM models (SheetRecord, SyncLog)
    ├── services/
    │   ├── __init__.py
    │   ├── sync_service.py  # Core diff engine, deduplication, and event staging
    │   └── maintenance.py   # Automated log cleanup routines
    └── utils/
        ├── __init__.py
        └── sheet_helpers.py # CSV URL builders, key generators, and dictionary diff helpers
```

---

## 🛠️ Tech Stack

* **Language:** Python 3.12+
* **Data Processing:** Pandas, NumPy
* **Database & ORM:** PostgreSQL, SQLAlchemy 2.0, Psycopg
* **Configuration:** python-dotenv

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone [https://github.com/your-username/sheets-postgres-diff-sync.git](https://github.com/your-username/sheets-postgres-diff-sync.git)
cd sheets-postgres-diff-sync
```

### 2. Create a virtual environment & install dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install pandas sqlalchemy psycopg[binary] python-dotenv
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory:
```env
DB_USER=postgres
DB_PASS=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=delegate_processing

SHEET_ID=your_google_sheet_id
DAYS_TO_KEEP_LOGS=15
```

### 4. Configure Sheet Mappings
Define your tabs, `gid` identifiers, header row index, and primary key columns inside `src/config/constants.py`:

```python
SHEET_CONFIG = {
    "ASIGN": {
        "gid": "0",
        "pk_columns": ["CustomOrder"],
        "header_row": 1,  # 0-indexed (Row 2 in Excel)
    },
    "EXCEPCIONES": {
        "gid": "1072759729",
        "pk_columns": ["Entidad", "Persona"],
        "header_row": 0,
    },
}
```

---

## ▶️ Usage

Run the synchronization pipeline manually or schedule it via `cron` / task scheduler:

```bash
python main.py
```

### Execution Flow
1. Verifies and initializes PostgreSQL tables (`sheet_records` and `sync_logs`).
2. Downloads each configured tab as CSV and normalizes `NaN`/`NaT` values to SQL `NULL`.
3. Filters duplicate primary keys and logs `DUPLICATE_WARNING` entries.
4. Compares incoming rows against active database records (`is_active = True`).
5. Commits changes transactionally and stages `INSERT`, `UPDATE`, and `DELETE` event payloads.
6. Purges audit logs older than `DAYS_TO_KEEP_LOGS`.