from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid


class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1, description="Content of the comment.")


class CommentResponse(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    user_id: uuid.UUID
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)