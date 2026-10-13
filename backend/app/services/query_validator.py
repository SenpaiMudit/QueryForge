"""
QueryForge - Query Validator Service
Combines fast regex-based completeness check with optional AI fallback.
"""
from app.utils.sql_parser import check_completeness
from app.models.schemas import ValidateResponse


def validate_query(query: str, use_ai: bool = False) -> ValidateResponse:
    """
    Check if a SQL query is syntactically complete.
    Uses fast regex rules first; optionally falls back to AI.
    """
    query = query.strip()

    if not query:
        return ValidateResponse(
            is_complete=False,
            is_valid=False,
            missing_part="a SQL query",
            hint="Start typing your SQL query.",
            example="SELECT * FROM table_name;",
        )

    # Fast regex check
    result = check_completeness(query)

    if not result["is_complete"] and use_ai:
        # Fallback to Gemini for more nuanced checking
        try:
            from app.services.ai_service import ai_validate
            ai_result = ai_validate(query)
            return ValidateResponse(**ai_result)
        except Exception:
            pass  # Fall through to regex result

    return ValidateResponse(
        is_complete=result["is_complete"],
        is_valid=result["is_complete"],
        missing_part=result.get("missing"),
        hint=result.get("hint"),
        example=result.get("example"),
    )
