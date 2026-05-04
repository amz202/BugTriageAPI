import uuid
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.client import get_db
from app.database.model import Ticket, TicketAssignment
from app.schemas.request import TicketCreate
from app.schemas.response import TicketResponse
from app.services.predictor import predictor
from app.core.config import AUTO_ASSIGN_THRESHOLD


router = APIRouter(prefix="/api/v1", tags=["tickets"])
logger = logging.getLogger(__name__)


async def dispatch_assignment_notification(ticket_id: uuid.UUID, label: str):
    """
    Background task to handle simulated email dispatch.
    Executes outside the main request-response cycle.
    """
    logger.info(f"Simulating email dispatch for Ticket {ticket_id} routed to {label} team.")
    # Future integration: SMTP or Transactional Email API logic here.


@router.post("/tickets", response_model=TicketResponse)
async def create_and_route_ticket(
        payload: TicketCreate,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    """
    Ingests a bug report, executes multi-task inference, routes based on
    confidence threshold, and persists the stateful ticket lifecycle.
    """
    # 1. Execute Inference Pipeline
    try:
        combined_text = f"{payload.title}\n\n{payload.description}"
        ml_results = await predictor.predict_async(combined_text)
    except Exception as e:
        logger.error(f"Inference engine failure: {str(e)}")
        raise HTTPException(status_code=503, detail="Machine learning service unavailable.")

    # 2. State Resolution Logic
    confidence = ml_results["confidence_score"]
    predicted_component = ml_results["predicted_component"]

    if confidence >= AUTO_ASSIGN_THRESHOLD:
        ticket_status = "assigned"
        assigned_label = predicted_component
    else:
        ticket_status = "manual_review"
        assigned_label = "unassigned"

    # 3. Database Transaction & State Persistence
    try:
        new_ticket = Ticket(
            title=payload.title,
            description=payload.description,
            reported_time=payload.reported_time,
            predicted_component=predicted_component,
            confidence_score=confidence,
            priority=ml_results["priority"],
            resolution_time_days=ml_results["resolution_time_days"],
            attention_weights=ml_results["attention_weights"],
            status=ticket_status
        )
        db.add(new_ticket)
        await db.flush()  # Flush to generate the ticket ID for the assignment relation

        new_assignment = TicketAssignment(
            ticket_id=new_ticket.id,
            assigned_label_name=assigned_label,
            # TODO: Replace with actual routing query once Users/Auth are implemented
            assigned_to_user_id=None
        )
        db.add(new_assignment)

        await db.commit()
        await db.refresh(new_ticket)
    except Exception as e:
        await db.rollback()
        logger.error(f"Database transaction failure: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to persist ticket state.")

    # 4. Asynchronous Notification Dispatch
    if ticket_status == "assigned":
        background_tasks.add_task(dispatch_assignment_notification, new_ticket.id, assigned_label)

    return new_ticket