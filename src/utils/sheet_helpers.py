import pandas as pd

def get_google_sheet_csv_url(sheet_id: str, gid: str) -> str:
    """Generates the direct CSV download URL for a specific Google Sheet tab."""
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

def generate_record_key(row: pd.Series, pk_columns: list) -> str:
    """Generates a string key from the specified primary key columns."""
    return "|".join([str(row.get(col, "")).strip() for col in pk_columns])

def get_row_differences(old_data: dict, new_data: dict) -> dict:
    """Compares two dictionaries and returns the differences."""
    differences = {}
    
    for key, new_val in new_data.items():
        old_val = old_data.get(key)
        if old_val != new_val:
            differences[key] = {"old": old_val, "new": new_val}
            
    for key, old_val in old_data.items():
        if key not in new_data:
            differences[key] = {"old": old_val, "new": None, "status": "column_removed"}
            
    return differences