from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import uuid

from app.core.dependencies import get_current_user
from app.database.client import get_db
from app.database.model import Label, User, UserLabel
from app.schemas.auth import LabelResponse
from app.schemas.teams import UserLabelAssign

router = APIRouter(
    tags=["Labels & Expertise"],
    dependencies=[Depends(get_current_user)]
)
@router.get("/api/v1/labels", response_model=List[LabelResponse])
async def get_labels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Label))
    return result.scalars().all()

@router.post("/api/v1/users/{user_id}/labels", status_code=status.HTTP_201_CREATED)
async def assign_label_to_user(
    user_id: uuid.UUID,
    label_in: UserLabelAssign,
    db: AsyncSession = Depends(get_db)
):
    # 1. Validate User
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # 2. Validate Label
    label_result = await db.execute(select(Label).where(Label.id == label_in.label_id))
    label = label_result.scalars().first()
    if not label:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found")

    # 3. Check for Existing Assignment
    link_result = await db.execute(
        select(UserLabel).where(
            UserLabel.user_id == user_id,
            UserLabel.label_id == label_in.label_id
        )
    )
    if link_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Label already assigned to this user"
        )

    # 4. Create Association
    user_label = UserLabel(user_id=user_id, label_id=label_in.label_id)
    db.add(user_label)
    await db.commit()

    return {"status": "success", "message": f"Expertise '{label.name}' assigned."}