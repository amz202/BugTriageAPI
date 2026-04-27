from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
import uuid


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Strong password for user account.")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LabelResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    team_id: Optional[uuid.UUID]
    labels: List[LabelResponse] = []

    model_config = ConfigDict(from_attributes=True)