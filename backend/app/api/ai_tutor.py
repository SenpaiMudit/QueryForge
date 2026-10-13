"""
QueryForge - AI Tutor API Routes
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    NL2SQLRequest, NL2SQLResponse,
    ExplainRequest, ExplainResponse,
    FixRequest, FixResponse,
    OptimizeRequest, OptimizeResponse,
    ValidateRequest, ValidateResponse,
)
from app.services import ai_service, schema_reader, db_manager

router = APIRouter(prefix="/api/ai", tags=["ai-tutor"])


def _get_schema(db_id: str):
    try:
        if db_manager.database_exists(db_id):
            return schema_reader.get_schema(db_id)
    except Exception:
        pass
    return None


@router.post("/nl2sql", response_model=NL2SQLResponse)
async def nl_to_sql(body: NL2SQLRequest):
    try:
        schema = _get_schema(body.db_id)
        result = ai_service.nl_to_sql(body.natural_language, schema)
        return NL2SQLResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.post("/explain", response_model=ExplainResponse)
async def explain(body: ExplainRequest):
    try:
        schema = _get_schema(body.db_id)
        result = ai_service.explain_query(body.query, schema)
        return ExplainResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.post("/fix", response_model=FixResponse)
async def fix(body: FixRequest):
    try:
        schema = _get_schema(body.db_id)
        result = ai_service.fix_query(body.query, body.error_message, schema)
        return FixResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize(body: OptimizeRequest):
    try:
        schema = _get_schema(body.db_id)
        result = ai_service.optimize_query(body.query, schema)
        return OptimizeResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.post("/validate", response_model=ValidateResponse)
async def ai_validate(body: ValidateRequest):
    try:
        result = ai_service.ai_validate(body.query)
        return ValidateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
