from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.dependencies import get_current_user
from app.database.client import get_db
from app.database.model import Ticket, User, Label, TicketAssignment
from app.schemas.ticket import TicketCreate, TicketDetailResponse
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import uuid

from app.database.model import Ticket, TicketAssignment
from app.schemas.ticket import TicketListResponse, TicketDetailResponse, TicketUpdate

router = APIRouter(
    prefix="/api/v1/tickets",
    tags=["Tickets"],
    dependencies=[Depends(get_current_user)]
)

@router.post("", response_model=TicketDetailResponse)
async def ingest_ticket(ticket_in: TicketCreate, db: AsyncSession = Depends(get_db)):
    # 1. Execute Deep Learning Inference (CodeBERT)
    # prediction = await predict_bug_attributes(ticket_in.title, ticket_in.description)

    # Mocking prediction for structural demonstration
    predicted_component = "network"
    confidence = 0.92

    # 2. Instantiate Ticket
    new_ticket = Ticket(
        title=ticket_in.title,
        description=ticket_in.description,
        reported_time=ticket_in.reported_time,
        predicted_component=predicted_component,
        confidence_score=confidence,
        status="assigned"
    )
    db.add(new_ticket)
    await db.flush()  # Flush to generate ticket ID

    # 3. Dynamic Assignment Logic via Clean Architecture
    # Locate an available user possessing the required expertise label
    stmt = select(User).join(User.labels).where(Label.name == predicted_component).limit(1)
    result = await db.execute(stmt)
    assigned_user = result.scalars().first()

    if assigned_user:
        assignment = TicketAssignment(
            ticket_id=new_ticket.id,
            assigned_to_user_id=assigned_user.id,
            assigned_label_name=predicted_component
        )
        db.add(assignment)
    else:
        new_ticket.status = "pending_triage"  # Fallback if no matching user is found

    await db.commit()
    await db.refresh(new_ticket)

    return new_ticket


@router.get("", response_model=List[TicketListResponse])
async def list_tickets(
        skip: int = 0,
        limit: int = 20,
        db: AsyncSession = Depends(get_db)
):
    """
    Retrieves a paginated list of tickets.
    Uses the TicketListResponse schema to automatically exclude heavy ML JSON payloads.
    """
    stmt = select(Ticket).order_by(Ticket.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(ticket_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the full detail view of a specific ticket, including attention_weights.
    """
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalars().first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return ticket


@router.patch("/{ticket_id}", response_model=TicketDetailResponse)
async def update_ticket(
        ticket_id: uuid.UUID,
        update_data: TicketUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    Allows manual triage overrides for status and assignment.
    """
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalars().first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    if update_data.status:
        ticket.status = update_data.status

    if update_data.assigned_to_user_id:
        # Check for existing assignment
        assign_result = await db.execute(
            select(TicketAssignment).where(TicketAssignment.ticket_id == ticket_id)
        )
        assignment = assign_result.scalars().first()

        if assignment:
            assignment.assigned_to_user_id = update_data.assigned_to_user_id
        else:
            # Create manual assignment if none exists
            new_assignment = TicketAssignment(
                ticket_id=ticket_id,
                assigned_to_user_id=update_data.assigned_to_user_id,
                assigned_label_name="manual_override"
            )
            db.add(new_assignment)

        ticket.status = "assigned"

    await db.commit()
    await db.refresh(ticket)
    return ticket