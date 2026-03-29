from pydantic import BaseModel
from typing import Dict, Any

class PredictionResponse(BaseModel):
    """
    Defines the structured output returned to the client.
    """
    status: str
    predicted_component: str
    confidence_score: float
    log_id: str  # The reference ID from Supabase
    metadata: Dict[str, Any] = {}

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "predicted_component": "ui",
                "confidence_score": 0.89,
                "log_id": "uuid-1234-5678",
                "metadata": {
                    "processing_time_ms": 45.2
                }
            }
        }