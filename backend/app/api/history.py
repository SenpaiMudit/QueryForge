"""
QueryForge - Query History API Routes
"""
from fastapi import APIRouter, HTTPException
from app.services import history_manager, db_manager

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/{db_id}")
async def get_history(db_id: str):
    if not db_manager.database_exists(db_id):
        raise HTTPException(status_code=404, detail="Database not found.")
    return history_manager.get_history(db_id)


@router.delete("/{db_id}")
async def clear_history(db_id: str):
    if not db_manager.database_exists(db_id):
        raise HTTPException(status_code=404, detail="Database not found.")
    history_manager.clear_history(db_id)
    return {"message": "History cleared."}
