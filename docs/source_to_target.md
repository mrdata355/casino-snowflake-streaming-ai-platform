# Source-to-Target Map

| Source | Contract | Bronze | Silver | Gold / Feature | Grain |
|---|---|---|---|---|---|
| Slot event broker | `contracts/slot_event.schema.json` | `BRONZE.SLOT_EVENTS_RAW` | `SILVER_SLOT_EVENTS` | `FACT_SLOT_PERFORMANCE_5MIN` | machine + 5-minute window |
| Gaming transactions | `contracts/game_transaction.schema.json` | `BRONZE.GAME_TRANSACTIONS_RAW` | `FACT_GAME_TRANSACTION_CLEAN` | `FACT_GAME_REVENUE_DAILY` | property + location + game + gaming day |
| Loyalty profile | versioned player contract | `BRONZE.LOYALTY_PROFILE_RAW` | `DIM_PLAYER_SCD2` | `FP_PLAYER_VALUE_DAILY` | player + analysis date |
| Model output | `contracts/model_score.schema.json` | `OPS.MODEL_SCORE_INGEST` | validated scoring output | governed API and monitoring view | entity + model version + score time |

All joins across gaming, hotel, POS, labor, and marketing domains must use governed identity and location mappings. Direct fact-to-fact joins are prohibited unless each input has first been aggregated to the target grain.
