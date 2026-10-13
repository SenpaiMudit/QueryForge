"""
QueryForge - Database API Routes
Handles DB creation, file upload, query execution, schema, and deletion.
"""
import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse

from app.core.config import settings
from app.models.schemas import (
    CreateDBRequest, CreateDBResponse,
    UploadResponse, QueryRequest, QueryResult,
    DatabaseSchema, ValidateRequest, ValidateResponse,
)
from app.services import db_manager
from app.services.query_executor import execute_query
from app.services.schema_reader import get_schema
from app.services.csv_importer import import_csv
from app.services.sql_importer import import_sql_file
from app.services.query_validator import validate_query
from app.services.history_manager import record_query
from app.utils.file_helpers import (
    is_allowed_file, sanitize_filename, check_file_size, get_file_type
)

router = APIRouter(prefix="/api/db", tags=["database"])


# ─────────────────────────────────────────────────────────────────────────────
# Create blank database
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/create", response_model=CreateDBResponse)
async def create_database(body: CreateDBRequest):
    info = db_manager.create_database(body.name)
    db_id = info["db_id"]
    # Rename file to include name
    old_path = db_manager.get_db_path(db_id)
    db_manager.save_database_with_name(db_id, body.name, str(old_path))
    if old_path.exists() and str(old_path) != str(db_manager.get_db_path(db_id)):
        old_path.unlink(missing_ok=True)
    return CreateDBResponse(
        db_id=db_id,
        db_name=body.name,
        message=f"Database '{body.name}' created successfully.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Upload file
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename or "upload"

    if not is_allowed_file(filename):
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: .csv, .sql, .sqlite, .db"
        )

    safe_name = sanitize_filename(filename)
    file_type = get_file_type(safe_name)

    # Save to upload staging area
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / f"{uuid.uuid4()}_{safe_name}"

    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        if not check_file_size(str(temp_path)):
            temp_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        db_id = str(uuid.uuid4())
        db_name = Path(safe_name).stem
        tables_created = []

        if file_type == "csv":
            # Create a blank db then import CSV
            info = db_manager.create_database(db_name)
            db_id = info["db_id"]
            # Rename with name
            old = db_manager.get_db_path(db_id)
            db_manager.save_database_with_name(db_id, db_name, str(old))
            if old.exists():
                old.unlink(missing_ok=True)
            tables_created = import_csv(db_id, str(temp_path))

        elif file_type == "sql":
            info = db_manager.create_database(db_name)
            db_id = info["db_id"]
            old = db_manager.get_db_path(db_id)
            db_manager.save_database_with_name(db_id, db_name, str(old))
            if old.exists():
                old.unlink(missing_ok=True)
            result = import_sql_file(db_id, str(temp_path))
            if not result["success"]:
                raise HTTPException(status_code=400, detail=f"SQL import errors: {result['errors']}")
            schema = get_schema(db_id)
            tables_created = [t.name for t in schema.tables]

        elif file_type == "sqlite":
            db_manager.save_database_with_name(db_id, db_name, str(temp_path))
            schema = get_schema(db_id)
            tables_created = [t.name for t in schema.tables]

        return UploadResponse(
            db_id=db_id,
            db_name=db_name,
            tables_created=tables_created,
            message=f"Uploaded '{safe_name}' successfully. {len(tables_created)} table(s) available.",
        )

    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Execute SQL query
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/execute", response_model=QueryResult)
async def execute(body: QueryRequest):
    if not db_manager.database_exists(body.db_id):
        raise HTTPException(status_code=404, detail="Database not found.")

    result = execute_query(body.db_id, body.query, body.limit)

    # Record in history
    try:
        record_query(
            db_id=body.db_id,
            query=body.query,
            status=result.status,
            statement_type=result.statement_type,
            rows_returned=result.row_count,
            rows_affected=result.rows_affected,
            execution_time_ms=result.execution_time_ms,
            error=result.error,
        )
    except Exception:
        pass

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Validate query (completeness check)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/validate", response_model=ValidateResponse)
async def validate(body: ValidateRequest):
    return validate_query(body.query)


# ─────────────────────────────────────────────────────────────────────────────
# Get database schema
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/schema/{db_id}", response_model=DatabaseSchema)
async def schema(db_id: str):
    if not db_manager.database_exists(db_id):
        raise HTTPException(status_code=404, detail="Database not found.")
    return get_schema(db_id)


# ─────────────────────────────────────────────────────────────────────────────
# List all databases
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/list")
async def list_databases():
    return db_manager.list_databases()


# ─────────────────────────────────────────────────────────────────────────────
# Delete database
# ─────────────────────────────────────────────────────────────────────────────
@router.delete("/{db_id}")
async def delete_database(db_id: str):
    if not db_manager.database_exists(db_id):
        raise HTTPException(status_code=404, detail="Database not found.")
    db_manager.delete_database(db_id)
    return {"message": "Database deleted."}
