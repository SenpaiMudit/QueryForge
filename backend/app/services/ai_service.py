"""
QueryForge - AI Service (Google Gemini)
Wraps google-generativeai SDK for NL→SQL, explain, fix, optimize.
"""
import re
import google.generativeai as genai
from app.core.config import settings
from app.models.schemas import DatabaseSchema


def _configure():
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/app/apikey")
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)


def _schema_to_text(schema: DatabaseSchema | None) -> str:
    if not schema:
        return "No schema available."
    lines = [f"Database: {schema.db_name}", "Tables:"]
    for table in schema.tables:
        cols = ", ".join(
            f"{c.name} {c.type}{'(PK)' if c.is_primary_key else ''}"
            for c in table.columns
        )
        lines.append(f"  - {table.name}({cols})  [{table.row_count} rows]")
    return "\n".join(lines)


def _extract_sql(text: str) -> str:
    """Pull out SQL from markdown code block if present."""
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


# ──────────────────────────────────────────────────────────────────────────────
# NL → SQL
# ──────────────────────────────────────────────────────────────────────────────
def nl_to_sql(natural_language: str, schema: DatabaseSchema | None = None) -> dict:
    model = _configure()
    schema_text = _schema_to_text(schema)

    prompt = f"""You are an expert SQLite query writer helping a student learn SQL.

Database schema:
{schema_text}

Convert this English request into a valid SQLite SQL query:
"{natural_language}"

Rules:
- Write ONLY valid SQLite SQL.
- Use the exact table and column names from the schema above.
- Return the SQL query inside a ```sql code block.
- After the code block, write a brief student-friendly explanation (2-3 sentences) of what the query does and which SQL concepts it uses.

Format:
```sql
YOUR_QUERY_HERE
```
Explanation: ...
"""
    response = model.generate_content(prompt)
    text = response.text.strip()

    sql_part = _extract_sql(text)
    explanation = ""
    if "Explanation:" in text:
        explanation = text.split("Explanation:", 1)[1].strip()
    elif "```" in text:
        after_code = text.split("```")[-1].strip()
        explanation = after_code if after_code else "Query generated successfully."

    return {
        "sql": sql_part,
        "explanation": explanation or "Here is the SQL query for your request.",
        "confidence": 0.95,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Explain Query
# ──────────────────────────────────────────────────────────────────────────────
def explain_query(query: str, schema: DatabaseSchema | None = None) -> dict:
    model = _configure()
    schema_text = _schema_to_text(schema)

    prompt = f"""You are a SQL tutor explaining queries to a beginner student.

Database schema:
{schema_text}

Explain this SQL query in simple, friendly language:
```sql
{query}
```

Provide:
1. A plain-English summary of what this query does (1-2 sentences).
2. A clause-by-clause breakdown. For each SQL clause used (SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY, HAVING, etc.), explain what it does in this specific query.
3. Up to 3 tips or things the student should know about this query.

Format your response as:
SUMMARY: ...
CLAUSES:
- SELECT: ...
- FROM: ...
(etc.)
TIPS:
- ...
"""
    response = model.generate_content(prompt)
    text = response.text.strip()

    summary = ""
    clause_breakdown = {}
    tips = []

    # Parse summary
    if "SUMMARY:" in text:
        summary = text.split("SUMMARY:", 1)[1].split("CLAUSES:", 1)[0].strip()

    # Parse clauses
    if "CLAUSES:" in text:
        clause_section = text.split("CLAUSES:", 1)[1].split("TIPS:", 1)[0].strip()
        for line in clause_section.split("\n"):
            line = line.strip().lstrip("- ")
            if ":" in line:
                key, val = line.split(":", 1)
                clause_breakdown[key.strip()] = val.strip()

    # Parse tips
    if "TIPS:" in text:
        tips_section = text.split("TIPS:", 1)[1].strip()
        for line in tips_section.split("\n"):
            line = line.strip().lstrip("- ")
            if line:
                tips.append(line)

    if not summary:
        summary = text[:300]

    return {
        "explanation": summary,
        "clause_breakdown": clause_breakdown,
        "suggestions": tips[:3],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Fix Broken Query
# ──────────────────────────────────────────────────────────────────────────────
def fix_query(query: str, error_message: str, schema: DatabaseSchema | None = None) -> dict:
    model = _configure()
    schema_text = _schema_to_text(schema)

    prompt = f"""You are a SQL debugger helping a student fix a broken SQLite query.

Database schema:
{schema_text}

Broken query:
```sql
{query}
```

Error message:
{error_message}

Fix the query and explain what was wrong in simple terms a student can understand.

Format:
FIXED_QUERY:
```sql
CORRECTED_QUERY_HERE
```
EXPLANATION: What was wrong and what you changed.
CHANGES:
- change 1
- change 2
"""
    response = model.generate_content(prompt)
    text = response.text.strip()

    fixed_sql = ""
    explanation = ""
    changes = []

    if "FIXED_QUERY:" in text:
        after_fixed = text.split("FIXED_QUERY:", 1)[1]
        fixed_sql = _extract_sql(after_fixed.split("EXPLANATION:", 1)[0])

    if "EXPLANATION:" in text:
        explanation = text.split("EXPLANATION:", 1)[1].split("CHANGES:", 1)[0].strip()

    if "CHANGES:" in text:
        changes_section = text.split("CHANGES:", 1)[1].strip()
        for line in changes_section.split("\n"):
            line = line.strip().lstrip("- ")
            if line:
                changes.append(line)

    return {
        "fixed_query": fixed_sql or query,
        "explanation": explanation or "The query was fixed.",
        "changes_made": changes[:5],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Optimize Query
# ──────────────────────────────────────────────────────────────────────────────
def optimize_query(query: str, schema: DatabaseSchema | None = None) -> dict:
    model = _configure()
    schema_text = _schema_to_text(schema)

    prompt = f"""You are a SQLite performance expert reviewing a student's SQL query.

Database schema:
{schema_text}

Query to optimize:
```sql
{query}
```

Provide:
1. An optimized version of the query if meaningful improvements are possible (otherwise say it's already efficient).
2. A list of specific optimization suggestions (indexes, avoiding SELECT *, using EXISTS vs IN, etc.).
3. A brief explanation of the improvements.

Format:
OPTIMIZED_QUERY:
```sql
QUERY_HERE
```
SUGGESTIONS:
- suggestion 1
- suggestion 2
EXPLANATION: ...
"""
    response = model.generate_content(prompt)
    text = response.text.strip()

    optimized = None
    suggestions = []
    explanation = ""

    if "OPTIMIZED_QUERY:" in text:
        after = text.split("OPTIMIZED_QUERY:", 1)[1]
        opt_sql = _extract_sql(after.split("SUGGESTIONS:", 1)[0])
        if opt_sql and opt_sql.upper() != query.upper():
            optimized = opt_sql

    if "SUGGESTIONS:" in text:
        sugg_section = text.split("SUGGESTIONS:", 1)[1].split("EXPLANATION:", 1)[0].strip()
        for line in sugg_section.split("\n"):
            line = line.strip().lstrip("- ")
            if line:
                suggestions.append(line)

    if "EXPLANATION:" in text:
        explanation = text.split("EXPLANATION:", 1)[1].strip()

    return {
        "optimized_query": optimized,
        "suggestions": suggestions[:5],
        "explanation": explanation or "Analysis complete.",
    }


# ──────────────────────────────────────────────────────────────────────────────
# AI-Enhanced Validate (incomplete query)
# ──────────────────────────────────────────────────────────────────────────────
def ai_validate(query: str) -> dict:
    model = _configure()

    prompt = f"""You are a SQL tutor checking if a SQL query is complete and valid.

Query: {query}

Is this query syntactically complete (not cut off mid-way)?
If incomplete, what part is missing and what hint + example would help a student?

Answer in this format:
IS_COMPLETE: true/false
MISSING: what is missing (if incomplete)
HINT: one sentence hint for the student
EXAMPLE: a short SQL example showing the completed part
"""
    response = model.generate_content(prompt)
    text = response.text.strip()

    is_complete = True
    missing = None
    hint = None
    example = None

    for line in text.split("\n"):
        if line.startswith("IS_COMPLETE:"):
            val = line.split(":", 1)[1].strip().lower()
            is_complete = val == "true"
        elif line.startswith("MISSING:"):
            missing = line.split(":", 1)[1].strip()
        elif line.startswith("HINT:"):
            hint = line.split(":", 1)[1].strip()
        elif line.startswith("EXAMPLE:"):
            example = line.split(":", 1)[1].strip()

    return {
        "is_complete": is_complete,
        "is_valid": is_complete,
        "missing_part": missing,
        "hint": hint,
        "example": example,
    }
