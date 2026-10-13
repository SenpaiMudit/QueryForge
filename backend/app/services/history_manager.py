"""
QueryForge - Query History Manager
Stores the last N queries per database as a JSON file.
"""
import json
import uuid
from pathlib import Path
from datetime import datetime
from app.core.config import settings
from app.models.schemas import QueryStatus, StatementType


def _history_path(db_id: str) -> Path:
    d = Path(settings.DATABASE_DIR) / "history"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{db_id}.json"


def _load(db_id: str) -> list:
    p = _history_path(db_id)
    if p.exists():
        with open(p, "r") as f:
            return json.load(f)
    return []


def _save(db_id: str, entries: list):
    with open(_history_path(db_id), "w") as f:
        json.dump(entries, f, default=str, indent=2)


def record_query(
    db_id: str,
    query: str,
    status: QueryStatus,
    statement_type: StatementType,
    rows_returned: int = 0,
    rows_affected: int = 0,
    execution_time_ms: float = 0,
    error: str | None = None,
) -> dict:
    entry = {
        "id": str(uuid.uuid4()),
        "db_id": db_id,
        "query": query[:2000],
        "status": status.value,
        "statement_type": statement_type.value,
        "rows_returned": rows_returned,
        "rows_affected": rows_affected,
        "execution_time_ms": execution_time_ms,
        "error": error,
        "executed_at": datetime.utcnow().isoformat(),
    }

    entries = _load(db_id)
    entries.insert(0, entry)

    # Enforce limit
    entries = entries[:settings.HISTORY_LIMIT]
    _save(db_id, entries)
    return entry


def get_history(db_id: str) -> list:
    return _load(db_id)


def clear_history(db_id: str):
    p = _history_path(db_id)
    if p.exists():
        p.unlink()
