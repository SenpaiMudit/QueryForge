"""
QueryForge - Snapshot API Routes
"""
from fastapi import APIRouter, HTTPException
from app.services import snapshot_manager, db_manager

router = APIRouter(prefix="/api/snapshot", tags=["snapshots"])


@router.get("/{db_id}")
async def list_snapshots(db_id: str):
    if not db_manager.database_exists(db_id):
        raise HTTPException(status_code=404, detail="Database not found.")
    return snapshot_manager.list_snapshots(db_id)


@router.post("/{db_id}/restore/{snapshot_id}")
async def restore_snapshot(db_id: str, snapshot_id: str):
    if not db_manager.database_exists(db_id):
        raise HTTPException(status_code=404, detail="Database not found.")
    try:
        return snapshot_manager.restore_snapshot(db_id, snapshot_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{db_id}/{snapshot_id}")
async def delete_snapshot(db_id: str, snapshot_id: str):
    snapshot_manager.delete_snapshot(snapshot_id, db_id)
    return {"message": "Snapshot deleted."}
