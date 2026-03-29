import time
import uuid
from fastapi import APIRouter, HTTPException

from app.repository.log_repository import LogRepository
from app.schemas.request import BugReportInput
from app.schemas.response import PredictionResponse
from app.services.predictor import predictor_service

router = APIRouter(prefix="/api/v1", tags=["inference"])

@router.post("/predict", response_model=PredictionResponse)
async def predict_bug_component(payload: BugReportInput):
    """
    Accepts bug report payload, executes inference, and returns predicted component.
    """
    start_time = time.perf_counter()

    try:
        # Delegate inference execution to the service layer
        result = predictor_service.predict(
            title=payload.issue_title,
            description=payload.description
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    try:
        # Persist transaction to db
        db_record = LogRepository.insert_prediction(
            issue_title=payload.issue_title,
            description=payload.description,
            predicted_component=result["predicted_component"],
            confidence_score=result["confidence_score"],
            execution_time_ms=execution_time_ms
        )
        log_id = str(db_record.get("id"))
    except Exception as e:
        # Fallback if database insertion fails.
        # Returns prediction to client but flags telemetry failure.
        log_id = "db-insert-failed"

    return PredictionResponse(
        status="success",
        predicted_component=result["predicted_component"],
        confidence_score=result["confidence_score"],
        log_id=log_id,
        metadata={
            "execution_time_ms": execution_time_ms
        }
    )