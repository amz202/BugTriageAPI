from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.future import select

from app.core.dependencies import get_current_user
from app.database.client import get_db
from app.database.model import Ticket
from app.schemas.analytics import AnalyticsOverviewResponse

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(db: AsyncSession = Depends(get_db)):
    """
    Returns aggregated metrics for the dashboard utilizing SQL-level aggregations.
    """
    # 1. Total Tickets Count
    total_result = await db.execute(select(func.count(Ticket.id)))
    total_tickets = total_result.scalar() or 0

    # 2. Pending Triage Count
    pending_result = await db.execute(
        select(func.count(Ticket.id)).where(Ticket.status == "pending_triage")
    )
    pending_count = pending_result.scalar() or 0

    # 3. Average ML Confidence
    confidence_result = await db.execute(select(func.avg(Ticket.confidence_score)))
    avg_confidence = confidence_result.scalar() or 0.0

    # 4. Average Predicted Resolution Time (Days)
    resolution_result = await db.execute(select(func.avg(Ticket.resolution_time_days)))
    avg_resolution = resolution_result.scalar() or 0.0

    return AnalyticsOverviewResponse(
        total_tickets=total_tickets,
        pending_triage_count=pending_count,
        average_ml_confidence=round(avg_confidence, 4),
        average_predicted_resolution_days=round(avg_resolution, 2)
    )