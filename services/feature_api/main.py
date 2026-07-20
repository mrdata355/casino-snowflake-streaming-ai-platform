from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from services.feature_api.models import FeatureResponse, PlayerFeatures
from services.feature_api.repository import get_player_features
from services.feature_api.security import require_principal

app = FastAPI(
    title="Casino Feature API",
    version="1.0.0",
    description="Governed point-in-time feature serving reference API.",
)

Principal = Annotated[dict, Depends(require_principal)]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/features/player/{player_id}", response_model=FeatureResponse)
def player_features(player_id: str, analysis_date: date, principal: Principal) -> FeatureResponse:
    del principal
    trace_id = uuid.uuid4().hex
    row = get_player_features(player_id, analysis_date)
    if row is None:
        raise HTTPException(status_code=404, detail="feature row not found")
    built_at = row["feature_built_at"]
    freshness = max(0, int((datetime.now(UTC) - built_at).total_seconds()))
    return FeatureResponse(
        data=PlayerFeatures(**row),
        freshness_seconds=freshness,
        trace_id=trace_id,
    )
