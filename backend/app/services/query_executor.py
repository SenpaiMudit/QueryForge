"""
QueryForge - Query Executor
Runs SQLite queries, formats results, tracks timing, and adds chart advice.
"""
import sqlite3
import time
from typing import Any
from app.services import db_manager
from app.services.chart_advisor import advise_chart
from app.services.snapshot_manager import create_snapshot
from app.utils.sql_parser import (
    detect_statement_type,
    is_destructive,
    split_statements,
    StatementType,
)
from app.models.schemas import (
    QueryResult,
    QueryStatus,
    QueryColumn,
    StatementType as SchemaStatementType,
)
from app.core.config import settings


def _infer_col_type(value: Any) -> str:
    """Infer display type from a sample Python value."""
    if value is None:
        return "text"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        # Naive date detection
        import re
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}')
        if date_pattern.match(value):
            return "date"
    return "text"


def execute_query(db_id: str, query: str, limit: int | None = None) -> QueryResult:
    """
    Execute one or more SQL statements against a database.
    Returns a QueryResult with rows, columns, chart config, and metadata.
    """
    query = query.strip()
    if not query:
        return QueryResult(
            status=QueryStatus.ERROR,
            statement_type=SchemaStatementType.OTHER,
            message="Empty query.",
            error="No query provided.",
        )

    # Split multi-statement queries; execute each in turn, return last result
    statements = split_statements(query)
    last_result = None

    for stmt in statements:
        last_result = _execute_single(db_id, stmt, limit)
        if last_result.status == QueryStatus.ERROR:
            return last_result

    return last_result or QueryResult(
        status=QueryStatus.ERROR,
        statement_type=SchemaStatementType.OTHER,
        error="No statements found.",
    )


def _execute_single(db_id: str, stmt: str, limit: int | None) -> QueryResult:
    stmt_type_raw = detect_statement_type(stmt)
    # Map util enum to schema enum (they share same values)
    stmt_type = SchemaStatementType(stmt_type_raw.value)

    # Auto-snapshot before destructive operations
    if is_destructive(stmt_type_raw):
        try:
            create_snapshot(db_id, trigger_query=stmt)
        except Exception:
            pass  # Don't block query if snapshot fails

    try:
        conn = db_manager.get_connection(db_id)
    except FileNotFoundError as e:
        return QueryResult(
            status=QueryStatus.ERROR,
            statement_type=stmt_type,
            error=str(e),
            message="Database not found.",
        )

    start = time.perf_counter()

    try:
        cursor = conn.cursor()

        if stmt_type == SchemaStatementType.SELECT or stmt.upper().startswith("PRAGMA"):
            # Apply row limit
            if limit is not None:
                effective_stmt = f"SELECT * FROM ({stmt}) LIMIT {limit}"
            elif settings.MAX_QUERY_ROWS:
                effective_stmt = f"SELECT * FROM ({stmt}) LIMIT {settings.MAX_QUERY_ROWS}"
            else:
                effective_stmt = stmt

            # For PRAGMA, run as-is
            if stmt.upper().startswith("PRAGMA"):
                effective_stmt = stmt

            cursor.execute(effective_stmt)
            raw_rows = cursor.fetchall()
            elapsed_ms = (time.perf_counter() - start) * 1000

            columns_raw = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = [list(row) for row in raw_rows]

            # Infer column types from first non-null value
            col_types = ["text"] * len(columns_raw)
            for row in rows:
                for i, val in enumerate(row):
                    if val is not None:
                        col_types[i] = _infer_col_type(val)

            columns = [
                QueryColumn(name=name, type=col_types[i])
                for i, name in enumerate(columns_raw)
            ]

            chart = advise_chart(columns, rows) if rows else None

            conn.close()
            return QueryResult(
                status=QueryStatus.SUCCESS,
                statement_type=stmt_type,
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=round(elapsed_ms, 2),
                chart=chart,
                message=f"{len(rows)} row(s) returned.",
            )

        else:
            # DML / DDL
            cursor.execute(stmt)
            conn.commit()
            elapsed_ms = (time.perf_counter() - start) * 1000
            rows_affected = cursor.rowcount if cursor.rowcount >= 0 else 0

            conn.close()
            return QueryResult(
                status=QueryStatus.SUCCESS,
                statement_type=stmt_type,
                rows_affected=rows_affected,
                execution_time_ms=round(elapsed_ms, 2),
                message=f"Query executed successfully. {rows_affected} row(s) affected.",
            )

    except sqlite3.OperationalError as e:
        conn.rollback()
        conn.close()
        return QueryResult(
            status=QueryStatus.ERROR,
            statement_type=stmt_type,
            error=str(e),
            message=f"SQL Error: {e}",
        )
    except sqlite3.IntegrityError as e:
        conn.rollback()
        conn.close()
        return QueryResult(
            status=QueryStatus.ERROR,
            statement_type=stmt_type,
            error=str(e),
            message=f"Integrity Error: {e}",
        )
    except Exception as e:
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        return QueryResult(
            status=QueryStatus.ERROR,
            statement_type=stmt_type,
            error=str(e),
            message=f"Unexpected error: {e}",
        )
