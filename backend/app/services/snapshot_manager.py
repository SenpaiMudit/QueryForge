"""
QueryForge - Snapshot Manager
Creates and restores SQLite database snapshots before destructive operations.
"""
import shutil
import uuid
import json
from pathlib import Path
from datetime import datetime
from app.core.config import settings


def _snap_dir(db_id: str) -> Path:
    d = Path(settings.SNAPSHOT_DIR) / db_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _meta_path(db_id: str) -> Path:
    return _snap_dir(db_id) / "snapshots.json"


def _load_meta(db_id: str) -> list:
    meta_path = _meta_path(db_id)
    if meta_path.exists():
        with open(meta_path, "r") as f:
            return json.load(f)
    return []


def _save_meta(db_id: str, snapshots: list):
    with open(_meta_path(db_id), "w") as f:
        json.dump(snapshots, f, default=str, indent=2)


def create_snapshot(db_id: str, trigger_query: str = "") -> dict:
    """Copy the current DB file into the snapshots directory."""
    from app.services.db_manager import get_db_path

    db_path = get_db_path(db_id)
    if not db_path.exists():
        raise FileNotFoundError(f"DB {db_id} not found for snapshot.")

    snap_id = str(uuid.uuid4())
    snap_file = _snap_dir(db_id) / f"{snap_id}.db"
    shutil.copy2(str(db_path), str(snap_file))

    stat = snap_file.stat()
    entry = {
        "snapshot_id": snap_id,
        "db_id": db_id,
        "trigger_query": trigger_query[:500],
        "created_at": datetime.utcnow().isoformat(),
        "size_bytes": stat.st_size,
    }

    snapshots = _load_meta(db_id)
    snapshots.insert(0, entry)

    # Enforce limit
    if len(snapshots) > settings.SNAPSHOT_LIMIT:
        # Delete oldest
        for old in snapshots[settings.SNAPSHOT_LIMIT:]:
            old_file = _snap_dir(db_id) / f"{old['snapshot_id']}.db"
            if old_file.exists():
                old_file.unlink()
        snapshots = snapshots[:settings.SNAPSHOT_LIMIT]

    _save_meta(db_id, snapshots)
    return entry


def list_snapshots(db_id: str) -> list:
    return _load_meta(db_id)


def restore_snapshot(db_id: str, snapshot_id: str) -> dict:
    """Overwrite the current DB file with a snapshot."""
    from app.services.db_manager import get_db_path

    snap_file = _snap_dir(db_id) / f"{snapshot_id}.db"
    if not snap_file.exists():
        raise FileNotFoundError(f"Snapshot {snapshot_id} not found.")

    db_path = get_db_path(db_id)
    shutil.copy2(str(snap_file), str(db_path))

    return {
        "success": True,
        "message": f"Database restored from snapshot {snapshot_id}.",
        "restored_at": datetime.utcnow().isoformat(),
    }


def delete_snapshot(snapshot_id: str, db_id: str) -> bool:
    snap_file = _snap_dir(db_id) / f"{snapshot_id}.db"
    if snap_file.exists():
        snap_file.unlink()

    snapshots = _load_meta(db_id)
    snapshots = [s for s in snapshots if s["snapshot_id"] != snapshot_id]
    _save_meta(db_id, snapshots)
    return True
