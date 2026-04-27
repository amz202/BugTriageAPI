from pydantic import BaseModel
from typing import Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

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


class TicketResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    reported_time: datetime
    created_at: datetime
    status: str

    # Machine Learning Outputs
    predicted_component: Optional[str] = None
    confidence_score: Optional[float] = None
    priority: Optional[str] = None
    resolution_time_days: Optional[float] = None
    attention_weights: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class TicketResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    reported_time: datetime
    created_at: datetime
    status: str

    # Machine Learning Outputs
    predicted_component: Optional[str] = None
    confidence_score: Optional[float] = None
    priority: Optional[str] = None
    resolution_time_days: Optional[float] = None
    attention_weights: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)