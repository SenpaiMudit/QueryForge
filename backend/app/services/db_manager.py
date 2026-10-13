"""
QueryForge - SQLite Database Session Manager
Each user database gets a UUID-based isolated .db file.
"""
import sqlite3
import uuid
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from app.core.config import settings


def _ensure_dirs():
    Path(settings.DATABASE_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.SNAPSHOT_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def create_database(name: str) -> dict:
    """Create a new blank SQLite database and return its metadata."""
    _ensure_dirs()
    db_id = str(uuid.uuid4())
    db_path = _get_db_path(db_id)

    # Touch the file to create it
    conn = sqlite3.connect(db_path)
    conn.close()

    return {
        "db_id": db_id,
        "db_name": name,
        "db_path": str(db_path),
        "created_at": datetime.utcnow(),
    }


def get_connection(db_id: str) -> sqlite3.Connection:
    """Return a sqlite3 connection for the given db_id."""
    db_path = _get_db_path(db_id)
    if not db_path.exists():
        raise FileNotFoundError(f"Database '{db_id}' not found.")

    conn = sqlite3.connect(str(db_path), timeout=settings.QUERY_TIMEOUT_SECONDS)
    conn.row_factory = sqlite3.Row
    # Enable foreign key enforcement
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def database_exists(db_id: str) -> bool:
    return _get_db_path(db_id).exists()


def delete_database(db_id: str) -> bool:
    db_path = _get_db_path(db_id)
    if db_path.exists():
        db_path.unlink()
        return True
    return False


def list_databases() -> list[dict]:
    """List all databases in the databases directory."""
    _ensure_dirs()
    dbs = []
    db_dir = Path(settings.DATABASE_DIR)
    for f in db_dir.glob("*.db"):
        # Name stored as filename stem format: {db_id}__{db_name}.db
        parts = f.stem.split("__", 1)
        db_id = parts[0]
        db_name = parts[1].replace("_", " ") if len(parts) > 1 else f.stem
        stat = f.stat()
        dbs.append({
            "db_id": db_id,
            "db_name": db_name,
            "created_at": datetime.utcfromtimestamp(stat.st_ctime),
            "size_bytes": stat.st_size,
        })
    return sorted(dbs, key=lambda x: x["created_at"], reverse=True)


def get_db_path(db_id: str) -> Path:
    return _get_db_path(db_id)


def _get_db_path(db_id: str) -> Path:
    """
    Looks for any .db file starting with db_id in the databases directory.
    Falls back to plain {db_id}.db if no named file found.
    """
    db_dir = Path(settings.DATABASE_DIR)
    db_dir.mkdir(parents=True, exist_ok=True)

    # Try named format first: {db_id}__{name}.db
    matches = list(db_dir.glob(f"{db_id}__*.db"))
    if matches:
        return matches[0]

    # Fallback: plain uuid.db
    return db_dir / f"{db_id}.db"


def save_database_with_name(db_id: str, name: str, source_path: str) -> str:
    """Copy a file into the database directory with proper naming."""
    _ensure_dirs()
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
    dest = Path(settings.DATABASE_DIR) / f"{db_id}__{safe_name}.db"
    shutil.copy2(source_path, str(dest))
    return str(dest)
