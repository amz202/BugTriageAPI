from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.client import get_db
from app.database.model import Ticket, User, Label, TicketAssignment
from app.schemas.ticket import TicketCreate, TicketDetailResponse

# from app.services.predictor import predict_bug_attributes  # Existing ML pipeline

router = APIRouter(prefix="/api/v1/tickets", tags=["Tickets"])


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