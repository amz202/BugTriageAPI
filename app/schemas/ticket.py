from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class TicketCreate(BaseModel):
    title: str = Field(
        ...,
        max_length=255,
        description="The title or summary of the bug report."
    )
    description: str = Field(
        ...,
        description="The full textual description, including stack traces or logs."
    )
    reported_time: Optional[datetime] = Field(
        default=None,
        description="The original timestamp of the report. Defaults to ingestion time if omitted."
    )

class TicketListResponse(BaseModel):
    """Excluded attention_weights for optimized pagination."""
    id: uuid.UUID
    title: str
    status: str
    predicted_component: Optional[str] = None
    priority: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketDetailResponse(BaseModel):
    """Full detail view including heavy ML inference data."""
    id: uuid.UUID
    title: str
    description: str
    status: str
    predicted_component: Optional[str] = None
    confidence_score: Optional[float] = None
    priority: Optional[str] = None
    resolution_time_days: Optional[float] = None
    attention_weights: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to_user_id: Optional[uuid.UUID] = None