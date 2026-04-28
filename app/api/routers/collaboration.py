from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from app.core.dependencies import get_current_user
from app.database.client import get_db
from app.database.model import Ticket, Comment, User
from app.schemas.collaboration import CommentCreate, CommentResponse

router = APIRouter(
    prefix="/api/v1/tickets",
    tags=["Collaboration"],
    dependencies=[Depends(get_current_user)]
)
@router.post("/{ticket_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
        ticket_id: uuid.UUID,
        comment_in: CommentCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Appends a new text comment to an existing ticket.
    Requires a valid JWT token.
    """
    ticket_result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    if not ticket_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Use current_user.id extracted securely from the JWT
    new_comment = Comment(
        ticket_id=ticket_id,
        user_id=current_user.id,
        text=comment_in.text
    )

    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    return new_comment