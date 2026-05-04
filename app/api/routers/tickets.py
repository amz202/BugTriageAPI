from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import uuid
import logging

from app.core.dependencies import get_current_user
from app.database.client import get_db
from app.database.model import Ticket, User, Label, TicketAssignment
from app.schemas.ticket import TicketCreate, TicketListResponse, TicketDetailResponse, TicketUpdate
from app.services.predictor import predictor
from app.api.routers.inference import dispatch_assignment_notification
from app.core.config import AUTO_ASSIGN_THRESHOLD

logger = logging.getLogger(__name__)



router = APIRouter(
    prefix="/api/v1/tickets",
    tags=["Tickets"],
    dependencies=[Depends(get_current_user)]
)


@router.post("", response_model=TicketDetailResponse)
async def ingest_ticket(
    ticket_in: TicketCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a ticket, run the model for multi-task predictions, persist the ticket,
    attempt automated assignment based on confidence and available users, and
    dispatch a background notification if assigned.
    """
    # 1. Run inference
    try:
        combined_text = f"{ticket_in.title}\n\n{ticket_in.description}"
        ml_results = await predictor.predict_async(combined_text)
    except Exception as e:
        logger.error(f"Inference failure: {e}")
        raise HTTPException(status_code=503, detail="Machine learning service unavailable.")

    predicted_component = ml_results.get("predicted_component", "other")
    confidence = float(ml_results.get("confidence_score", 0.0))
    priority = ml_results.get("priority")
    resolution_time_days = ml_results.get("resolution_time_days")
    attention_weights = ml_results.get("attention_weights")

    # 2. Resolve status & assignment intent
    assigned_label = "unassigned"
    ticket_status = "manual_review"
    if confidence >= AUTO_ASSIGN_THRESHOLD:
        assigned_label = predicted_component
        ticket_status = "assigned"
    else:
        ticket_status = "manual_review"

    # 3. Persist ticket + assignment in transaction
    try:
        new_ticket = Ticket(
            title=ticket_in.title,
            description=ticket_in.description,
            reported_time=ticket_in.reported_time,
            predicted_component=predicted_component,
            confidence_score=confidence,
            priority=priority,
            resolution_time_days=resolution_time_days,
            attention_weights=attention_weights,
            status=ticket_status
        )
        db.add(new_ticket)
        await db.flush()  # populate new_ticket.id

        # If confident, try to locate a user with the matching label
        if ticket_status == "assigned":
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
                # Keep status as 'assigned'
            else:
                # No matching user found despite high confidence
                new_ticket.status = "pending_triage"
                assignment = TicketAssignment(
                    ticket_id=new_ticket.id,
                    assigned_to_user_id=None,
                    assigned_label_name=predicted_component
                )
                db.add(assignment)
        else:
            # Low confidence -> manual review, mark unassigned
            assignment = TicketAssignment(
                ticket_id=new_ticket.id,
                assigned_to_user_id=None,
                assigned_label_name="unassigned"
            )
            db.add(assignment)

        await db.commit()
        await db.refresh(new_ticket)

    except Exception as e:
        await db.rollback()
        logger.error(f"Database transaction failure: {e}")
        raise HTTPException(status_code=500, detail="Failed to persist ticket state.")

    # 4. Background notification if assigned to a user
    # If an assignment exists and has a user id, notify
    try:
        assign_stmt = select(TicketAssignment).where(TicketAssignment.ticket_id == new_ticket.id)
        assign_res = await db.execute(assign_stmt)
        final_assignment = assign_res.scalars().first()
        if final_assignment and final_assignment.assigned_to_user_id:
            background_tasks.add_task(
                dispatch_assignment_notification,
                new_ticket.id,
                final_assignment.assigned_label_name
            )
    except Exception:
        # Non-fatal: log and continue returning the ticket
        logger.exception("Failed to schedule assignment notification")

    return new_ticket


@router.get("", response_model=List[TicketListResponse])
async def list_tickets(
        skip: int = 0,
        limit: int = 20,
        db: AsyncSession = Depends(get_db)
):
    stmt = select(Ticket).order_by(Ticket.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(ticket_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketDetailResponse)
async def update_ticket(
        ticket_id: uuid.UUID,
        update_data: TicketUpdate,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if update_data.status:
        ticket.status = update_data.status

    if update_data.assigned_to_user_id:
        assign_result = await db.execute(
            select(TicketAssignment).where(TicketAssignment.ticket_id == ticket_id)
        )
        assignment = assign_result.scalars().first()

        if assignment:
            assignment.assigned_to_user_id = update_data.assigned_to_user_id
        else:
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
