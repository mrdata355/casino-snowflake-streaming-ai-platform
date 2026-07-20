from datetime import date, datetime

from pydantic import BaseModel, Field


class PlayerFeatures(BaseModel):
    player_id: str
    analysis_date: date
    net_gaming_revenue_30d: float
    active_gaming_days_30d: int
    loyalty_tier_as_of_date: str | None
    feature_max_event_date: date | None
    feature_built_at: datetime


class FeatureResponse(BaseModel):
    data: PlayerFeatures
    freshness_seconds: int = Field(ge=0)
    trace_id: str
