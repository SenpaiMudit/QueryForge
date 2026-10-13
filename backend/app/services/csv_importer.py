"""
QueryForge - CSV Importer
Converts uploaded CSV files into SQLite tables using Pandas.
"""
import sqlite3
import pandas as pd
from pathlib import Path
from app.services import db_manager


def _sanitize_col_name(name: str) -> str:
    """Make column names SQL-safe."""
    import re
    name = re.sub(r'[^\w]', '_', str(name).strip())
    if name and name[0].isdigit():
        name = f"col_{name}"
    return name or "column"


def import_csv(db_id: str, csv_path: str, table_name: str | None = None) -> list[str]:
    """
    Import a CSV file into a SQLite table.
    Returns list of created table names.
    """
    path = Path(csv_path)
    if not table_name:
        # Use filename without extension as table name
        table_name = _sanitize_col_name(path.stem)

    # Read CSV
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="latin-1")

    # Sanitize column names
    df.columns = [_sanitize_col_name(c) for c in df.columns]

    # Remove fully empty rows
    df = df.dropna(how="all")

    db_path = str(db_manager.get_db_path(db_id))
    conn = sqlite3.connect(db_path)

    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()

    return [table_name]
