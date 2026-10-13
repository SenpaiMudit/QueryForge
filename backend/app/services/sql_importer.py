"""
QueryForge - SQL File Importer
Runs .sql script files against a SQLite database.
"""
import sqlite3
from app.services import db_manager


def import_sql_file(db_id: str, sql_path: str) -> dict:
    """
    Execute a .sql file against the given database.
    Returns dict with statements_run and any errors.
    """
    try:
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
    except UnicodeDecodeError:
        with open(sql_path, "r", encoding="latin-1") as f:
            sql_content = f.read()

    db_path = str(db_manager.get_db_path(db_id))
    conn = sqlite3.connect(db_path)
    errors = []
    statements_run = 0

    try:
        # executescript runs the whole file atomically
        conn.executescript(sql_content)
        conn.commit()
        # Count non-empty statements
        statements_run = len([
            s.strip() for s in sql_content.split(";")
            if s.strip() and not s.strip().startswith("--")
        ])
    except sqlite3.Error as e:
        errors.append(str(e))
        conn.rollback()
    finally:
        conn.close()

    return {
        "statements_run": statements_run,
        "errors": errors,
        "success": len(errors) == 0,
    }
