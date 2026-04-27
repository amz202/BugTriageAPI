from pydantic import BaseModel, Field
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any

class BugReportInput(BaseModel):
    """
    Defines the strict data contract for incoming bug classification requests.
    """
    issue_title: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="The summary or title of the bug report."
    )
    description: str = Field(
        ...,
        min_length=10,
        description="The detailed description, including stack traces or code snippets."
    )
    reported_time: Optional[str] = Field(
        None,
        description="Optional timestamp of when the bug was reported."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "issue_title": "UI freezes when clicking the submit button",
                "description": "When navigating to the dashboard and clicking submit, the page becomes unresponsive for 5 seconds. See attached console logs.",
                "reported_time": "2026-03-29T10:00:00Z"
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

class TicketCreate(BaseModel):
    title: str = Field(..., max_length=255, description="The title or summary of the bug report.")
    description: str = Field(..., description="The full textual description, including stack traces or logs.")
    reported_time: Optional[datetime] = Field(
        default=None,
        description="The original timestamp of the report. Defaults to ingestion time if omitted."
    )