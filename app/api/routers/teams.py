import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.dependencies import get_current_user
from app.database.client import get_db
from app.database.model import Team, User, Label
from app.schemas.teams import TeamCreate, TeamResponse, UserLabelAssign

router = APIRouter(
    prefix="/api/v1/teams",
    tags=["Teams"],
    dependencies=[Depends(get_current_user)]
)

@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(team_in: TeamCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.name == team_in.name))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name already exists"
        )

    new_team = Team(name=team_in.name)
    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)
    return new_team

@router.get("", response_model=List[TeamResponse])
async def get_teams(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team))
    return result.scalars().all()