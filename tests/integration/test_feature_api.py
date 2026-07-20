from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from services.feature_api import main


def test_health() -> None:
    response = TestClient(main.app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_player_feature_response(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setattr(
        main,
        "get_player_features",
        lambda player_id, analysis_date: {
            "player_id": player_id,
            "analysis_date": analysis_date,
            "net_gaming_revenue_30d": 950.0,
            "active_gaming_days_30d": 5,
            "loyalty_tier_as_of_date": "GOLD",
            "feature_max_event_date": date(2026, 7, 19),
            "feature_built_at": datetime.now(UTC),
        },
    )

    response = TestClient(main.app).get("/v1/features/player/P100?analysis_date=2026-07-20")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["player_id"] == "P100"
    assert body["data"]["loyalty_tier_as_of_date"] == "GOLD"
    assert body["trace_id"]
