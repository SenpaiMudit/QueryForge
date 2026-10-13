"""
QueryForge - Pydantic Request/Response Schemas
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class QueryStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    INCOMPLETE = "incomplete"

class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    TABLE = "table"
    NONE = "none"

class StatementType(str, Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"
    PRAGMA = "PRAGMA"
    OTHER = "OTHER"


# ──────────────────────────────────────────────
# Database Schemas
# ──────────────────────────────────────────────

class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool = True
    default: Optional[str] = None
    is_primary_key: bool = False

class ForeignKeyInfo(BaseModel):
    from_column: str
    to_table: str
    to_column: str

class TableInfo(BaseModel):
    name: str
    columns: List[ColumnInfo]
    row_count: int = 0
    foreign_keys: List[ForeignKeyInfo] = []

class DatabaseSchema(BaseModel):
    db_id: str
    db_name: str
    tables: List[TableInfo]
    total_tables: int

class DatabaseInfo(BaseModel):
    db_id: str
    db_name: str
    created_at: datetime
    size_bytes: int
    table_count: int


# ──────────────────────────────────────────────
# Query Schemas
# ──────────────────────────────────────────────

class QueryRequest(BaseModel):
    db_id: str
    query: str
    limit: Optional[int] = None

class QueryColumn(BaseModel):
    name: str
    type: str  # "number" | "text" | "date" | "boolean"

class ChartConfig(BaseModel):
    type: ChartType
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    title: str = ""

class QueryResult(BaseModel):
    status: QueryStatus
    statement_type: StatementType
    columns: List[QueryColumn] = []
    rows: List[List[Any]] = []
    row_count: int = 0
    rows_affected: int = 0
    execution_time_ms: float = 0
    chart: Optional[ChartConfig] = None
    message: str = ""
    error: Optional[str] = None


# ──────────────────────────────────────────────
# AI Tutor Schemas
# ──────────────────────────────────────────────

class NL2SQLRequest(BaseModel):
    natural_language: str
    db_id: str
    schema_context: Optional[str] = None

class NL2SQLResponse(BaseModel):
    sql: str
    explanation: str
    confidence: float = 1.0

class ExplainRequest(BaseModel):
    query: str
    db_id: str

class ExplainResponse(BaseModel):
    explanation: str
    clause_breakdown: Dict[str, str] = {}
    suggestions: List[str] = []

class FixRequest(BaseModel):
    query: str
    error_message: str
    db_id: str

class FixResponse(BaseModel):
    fixed_query: str
    explanation: str
    changes_made: List[str] = []

class OptimizeRequest(BaseModel):
    query: str
    db_id: str

class OptimizeResponse(BaseModel):
    optimized_query: Optional[str] = None
    suggestions: List[str] = []
    explanation: str = ""

class ValidateRequest(BaseModel):
    query: str

class ValidateResponse(BaseModel):
    is_complete: bool
    is_valid: bool
    missing_part: Optional[str] = None
    hint: Optional[str] = None
    example: Optional[str] = None


# ──────────────────────────────────────────────
# Upload Schemas
# ──────────────────────────────────────────────

class UploadResponse(BaseModel):
    db_id: str
    db_name: str
    tables_created: List[str]
    message: str

class CreateDBRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_\- ]+$')

class CreateDBResponse(BaseModel):
    db_id: str
    db_name: str
    message: str


# ──────────────────────────────────────────────
# History Schemas
# ──────────────────────────────────────────────

class QueryHistoryEntry(BaseModel):
    id: str
    db_id: str
    query: str
    status: QueryStatus
    statement_type: StatementType
    rows_returned: int = 0
    rows_affected: int = 0
    execution_time_ms: float = 0
    error: Optional[str] = None
    executed_at: datetime


# ──────────────────────────────────────────────
# Snapshot Schemas
# ──────────────────────────────────────────────

class SnapshotInfo(BaseModel):
    snapshot_id: str
    db_id: str
    trigger_query: str
    created_at: datetime
    size_bytes: int

class RestoreResponse(BaseModel):
    success: bool
    message: str
    restored_at: datetime
