from pydantic import BaseModel

class AnalyticsOverviewResponse(BaseModel):
    total_tickets: int
    pending_triage_count: int
    average_ml_confidence: float
    average_predicted_resolution_days: float