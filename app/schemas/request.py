from pydantic import BaseModel, Field
from typing import Optional

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