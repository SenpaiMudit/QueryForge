"""
QueryForge - Schema Reader
Introspects SQLite database tables, columns, types, PKs, and FKs.
"""
import sqlite3
from app.services import db_manager
from app.models.schemas import DatabaseSchema, TableInfo, ColumnInfo, ForeignKeyInfo


def get_schema(db_id: str) -> DatabaseSchema:
    """Return the full schema of a database."""
    conn = db_manager.get_connection(db_id)
    tables = []

    try:
        cursor = conn.cursor()

        # Get all user tables (exclude sqlite internal tables)
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """)
        table_names = [row[0] for row in cursor.fetchall()]

        for table_name in table_names:
            # Column info via PRAGMA
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            pragma_rows = cursor.fetchall()

            columns = []
            for row in pragma_rows:
                # row: (cid, name, type, notnull, dflt_value, pk)
                columns.append(ColumnInfo(
                    name=row[1],
                    type=row[2] if row[2] else "TEXT",
                    nullable=not bool(row[3]),
                    default=str(row[4]) if row[4] is not None else None,
                    is_primary_key=bool(row[5]),
                ))

            # Row count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\";")
                row_count = cursor.fetchone()[0]
            except Exception:
                row_count = 0

            # Foreign keys
            cursor.execute(f"PRAGMA foreign_key_list('{table_name}');")
            fk_rows = cursor.fetchall()
            foreign_keys = []
            for fk in fk_rows:
                # row: (id, seq, table, from, to, on_update, on_delete, match)
                foreign_keys.append(ForeignKeyInfo(
                    from_column=fk[3],
                    to_table=fk[2],
                    to_column=fk[4],
                ))

            tables.append(TableInfo(
                name=table_name,
                columns=columns,
                row_count=row_count,
                foreign_keys=foreign_keys,
            ))

    finally:
        conn.close()

    # Resolve db_name from file
    db_path = db_manager.get_db_path(db_id)
    stem = db_path.stem
    parts = stem.split("__", 1)
    db_name = parts[1].replace("_", " ") if len(parts) > 1 else stem

    return DatabaseSchema(
        db_id=db_id,
        db_name=db_name,
        tables=tables,
        total_tables=len(tables),
    )
