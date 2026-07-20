from __future__ import annotations

import os
from typing import Any

from services.common.snowflake import connection


def snowflake_options() -> dict[str, str]:
    required = {
        "sfURL": os.environ["SNOWFLAKE_HOST"],
        "sfUser": os.environ["SNOWFLAKE_USER"],
        "sfDatabase": os.environ["SNOWFLAKE_DATABASE"],
        "sfSchema": os.getenv("SNOWFLAKE_TEMP_SCHEMA", "TEMP"),
        "sfWarehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "sfRole": os.environ["SNOWFLAKE_ROLE"],
    }
    if password := os.getenv("SNOWFLAKE_PASSWORD"):
        required["sfPassword"] = password
    return required


def merge_slot_batch(batch_df: Any, batch_id: int) -> None:
    """Stage a micro-batch and merge by deterministic event_id.

    Spark retries may execute the same batch more than once. The staging table is
    overwritten for each batch and the target MERGE makes the sink replay-safe.
    """
    if batch_df.rdd.isEmpty():
        return

    stage_table = f"SLOT_EVENTS_BATCH_{batch_id}"
    (
        batch_df.write.format("net.snowflake.spark.snowflake")
        .options(**snowflake_options())
        .option("dbtable", stage_table)
        .mode("overwrite")
        .save()
    )

    database = os.environ["SNOWFLAKE_DATABASE"]
    with connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                MERGE INTO {database}.BRONZE.SLOT_EVENTS_RAW AS target
                USING {database}.TEMP.{stage_table} AS source
                  ON target.EVENT_ID = source.EVENT_ID
                WHEN MATCHED AND source.INGESTED_AT > target.INGESTED_AT THEN UPDATE SET
                  MACHINE_ID = source.MACHINE_ID,
                  PROPERTY_ID = source.PROPERTY_ID,
                  EVENT_TIME = source.EVENT_TIME,
                  EVENT_TYPE = source.EVENT_TYPE,
                  COIN_IN = source.COIN_IN,
                  PAYOUT = source.PAYOUT,
                  JACKPOT_AMOUNT = source.JACKPOT_AMOUNT,
                  PAYLOAD = source.PAYLOAD,
                  INGESTED_AT = source.INGESTED_AT
                WHEN NOT MATCHED THEN INSERT (
                  EVENT_ID, MACHINE_ID, PROPERTY_ID, EVENT_TIME, EVENT_TYPE,
                  COIN_IN, PAYOUT, JACKPOT_AMOUNT, PAYLOAD, INGESTED_AT
                ) VALUES (
                  source.EVENT_ID, source.MACHINE_ID, source.PROPERTY_ID,
                  source.EVENT_TIME, source.EVENT_TYPE, source.COIN_IN,
                  source.PAYOUT, source.JACKPOT_AMOUNT, source.PAYLOAD,
                  source.INGESTED_AT
                )
                """
            )
            cursor.execute(f"DROP TABLE IF EXISTS {database}.TEMP.{stage_table}")
        finally:
            cursor.close()
