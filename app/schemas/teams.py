from pydantic import BaseModel, Field, ConfigDict
import uuid

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)

class TeamResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

class UserLabelAssign(BaseModel):
    label_id: uuid.UUID