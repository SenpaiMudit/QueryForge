"""
QueryForge - SQL Parser Utility
Detects statement type and checks basic completeness.
"""
import re
from app.models.schemas import StatementType


# Keywords that indicate a DML/DDL change (require snapshot)
DESTRUCTIVE_STATEMENTS = {
    StatementType.INSERT,
    StatementType.UPDATE,
    StatementType.DELETE,
    StatementType.DROP,
    StatementType.ALTER,
}

# Keywords that refresh the schema explorer
SCHEMA_CHANGING_STATEMENTS = {
    StatementType.CREATE,
    StatementType.ALTER,
    StatementType.DROP,
}


def detect_statement_type(query: str) -> StatementType:
    """
    Return the primary statement type of the SQL query.
    Looks at the first meaningful keyword (ignoring comments).
    """
    # Strip comments
    clean = re.sub(r'--[^\n]*', '', query)          # single-line comments
    clean = re.sub(r'/\*.*?\*/', '', clean, flags=re.DOTALL)  # block comments
    clean = clean.strip().upper()

    if not clean:
        return StatementType.OTHER

    first_word = clean.split()[0] if clean.split() else ""

    mapping = {
        "SELECT": StatementType.SELECT,
        "INSERT": StatementType.INSERT,
        "UPDATE": StatementType.UPDATE,
        "DELETE": StatementType.DELETE,
        "CREATE": StatementType.CREATE,
        "ALTER": StatementType.ALTER,
        "DROP": StatementType.DROP,
        "PRAGMA": StatementType.PRAGMA,
    }
    return mapping.get(first_word, StatementType.OTHER)


def is_destructive(stmt_type: StatementType) -> bool:
    """Returns True if the statement modifies data (needs snapshot)."""
    return stmt_type in DESTRUCTIVE_STATEMENTS


def is_schema_changing(stmt_type: StatementType) -> bool:
    """Returns True if the statement changes the database schema."""
    return stmt_type in SCHEMA_CHANGING_STATEMENTS


def split_statements(sql: str) -> list[str]:
    """
    Split a multi-statement SQL string into individual statements.
    Naive split on ';', handles basic cases.
    """
    statements = []
    current = ""
    in_string = False
    string_char = None

    for char in sql:
        if in_string:
            current += char
            if char == string_char:
                in_string = False
        elif char in ("'", '"'):
            in_string = True
            string_char = char
            current += char
        elif char == ';':
            stmt = current.strip()
            if stmt:
                statements.append(stmt)
            current = ""
        else:
            current += char

    # Remaining content without trailing semicolon
    last = current.strip()
    if last:
        statements.append(last)

    return [s for s in statements if s]


# Patterns for detecting incomplete queries
INCOMPLETE_PATTERNS = [
    {
        "pattern": re.compile(r'^\s*SELECT\s*$', re.IGNORECASE),
        "missing": "column list after SELECT",
        "hint": "Specify which columns to retrieve. Use * for all columns.",
        "example": "SELECT * FROM table_name;"
    },
    {
        "pattern": re.compile(r'^\s*SELECT\s+.+\s*$', re.IGNORECASE),
        "check_fn": lambda q: 'from' not in q.lower(),
        "missing": "FROM clause",
        "hint": "Add FROM followed by the table name.",
        "example": "SELECT column FROM table_name;"
    },
    {
        "pattern": re.compile(r'\bWHERE\s*$', re.IGNORECASE),
        "missing": "condition after WHERE",
        "hint": "WHERE needs a condition to filter records.",
        "example": "WHERE column_name = 'value'"
    },
    {
        "pattern": re.compile(r'\bORDER\s+BY\s*$', re.IGNORECASE),
        "missing": "column name after ORDER BY",
        "hint": "Specify which column to sort by.",
        "example": "ORDER BY column_name ASC"
    },
    {
        "pattern": re.compile(r'\bGROUP\s+BY\s*$', re.IGNORECASE),
        "missing": "column name after GROUP BY",
        "hint": "Specify the column to group results by.",
        "example": "GROUP BY department"
    },
    {
        "pattern": re.compile(r'\bJOIN\s*$', re.IGNORECASE),
        "missing": "table name after JOIN",
        "hint": "Specify the table to join and an ON condition.",
        "example": "JOIN orders ON students.id = orders.student_id"
    },
    {
        "pattern": re.compile(r'\bINSERT\s+INTO\s*$', re.IGNORECASE),
        "missing": "table name after INSERT INTO",
        "hint": "Provide the target table name.",
        "example": "INSERT INTO students (name, age) VALUES ('Alice', 20);"
    },
    {
        "pattern": re.compile(r'\bUPDATE\s*$', re.IGNORECASE),
        "missing": "table name after UPDATE",
        "hint": "Specify the table to update.",
        "example": "UPDATE students SET grade = 'A' WHERE id = 1;"
    },
    {
        "pattern": re.compile(r'\bSET\s*$', re.IGNORECASE),
        "missing": "assignment after SET",
        "hint": "Provide column = value assignments after SET.",
        "example": "SET name = 'Bob', age = 21"
    },
]


def check_completeness(query: str) -> dict:
    """
    Check if a SQL query appears to be incomplete.
    Returns a dict with keys: is_complete, missing, hint, example
    """
    query_stripped = query.strip()

    if not query_stripped:
        return {"is_complete": False, "missing": "query", "hint": "Start typing a SQL query.", "example": "SELECT * FROM table_name;"}

    for rule in INCOMPLETE_PATTERNS:
        pattern_match = rule["pattern"].search(query_stripped)
        if pattern_match:
            # If there's a check_fn, use it for additional verification
            check_fn = rule.get("check_fn")
            if check_fn and not check_fn(query_stripped):
                continue
            return {
                "is_complete": False,
                "missing": rule["missing"],
                "hint": rule["hint"],
                "example": rule["example"],
            }

    return {"is_complete": True, "missing": None, "hint": None, "example": None}
