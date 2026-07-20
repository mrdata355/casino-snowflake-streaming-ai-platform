from __future__ import annotations

import os
from datetime import date

from services.common.snowflake import connection


def get_player_features(player_id: str, analysis_date: date) -> dict | None:
    database = os.getenv("SNOWFLAKE_DATABASE", "CASINO_DEV")
    table = f"{database}.FEATURES.FP_PLAYER_VALUE_DAILY"
    sql = f"""
        SELECT
            PLAYER_ID,
            ANALYSIS_DATE,
            NET_GAMING_REVENUE_30D,
            ACTIVE_GAMING_DAYS_30D,
            LOYALTY_TIER_AS_OF_DATE,
            FEATURE_MAX_EVENT_DATE,
            FEATURE_BUILT_AT
        FROM {table}
        WHERE PLAYER_ID = %s
          AND ANALYSIS_DATE = %s
    """
    with connection("feature_api.player_value") as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, (player_id, analysis_date))
            row = cur.fetchone()
            if not row:
                return None
            return dict(zip([column[0].lower() for column in cur.description], row, strict=True))
        finally:
            cur.close()
