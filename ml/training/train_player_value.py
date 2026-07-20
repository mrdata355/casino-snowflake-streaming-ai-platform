from __future__ import annotations

import json
import os
from pathlib import Path

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

NUMERIC_FEATURES = [
    "net_gaming_revenue_30d",
    "active_gaming_days_30d",
    "hotel_spend_30d",
    "food_beverage_spend_30d",
    "offer_redemptions_30d",
]
CATEGORICAL_FEATURES = ["loyalty_tier", "home_property_id"]
TARGET = "net_gaming_revenue_next_30d"


def load_training_frame(path: str | None = None) -> pd.DataFrame:
    if path:
        return pd.read_parquet(path)
    from services.common.snowflake import query_dataframe

    cutoff = os.environ.get("TRAINING_CUTOFF_DATE", "2026-06-30")
    return query_dataframe(
        f"""
        SELECT *
        FROM {os.environ['SNOWFLAKE_DATABASE']}.FEATURES.FP_PLAYER_VALUE_TRAINING
        WHERE LABEL_END_DATE <= %s
        """,
        params=(cutoff,),
    )


def train(frame: pd.DataFrame) -> dict[str, float]:
    required = set(NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET, "feature_timestamp"])
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing training columns: {sorted(missing)}")

    frame = frame.sort_values("feature_timestamp")
    split_index = int(len(frame) * 0.8)
    train_frame = frame.iloc[:split_index]
    test_frame = frame.iloc[split_index:]
    if train_frame.empty or test_frame.empty:
        raise ValueError("Time-based split requires at least five rows")

    numeric = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    preprocess = ColumnTransformer(
        [("numeric", numeric, NUMERIC_FEATURES), ("categorical", categorical, CATEGORICAL_FEATURES)]
    )
    model = Pipeline(
        [
            ("preprocess", preprocess),
            ("model", HistGradientBoostingRegressor(max_depth=6, learning_rate=0.05, random_state=42)),
        ]
    )

    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    model.fit(train_frame[features], train_frame[TARGET])
    predictions = model.predict(test_frame[features])
    metrics = {
        "mae": float(mean_absolute_error(test_frame[TARGET], predictions)),
        "rmse": float(root_mean_squared_error(test_frame[TARGET], predictions)),
        "train_rows": float(len(train_frame)),
        "test_rows": float(len(test_frame)),
    }

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "casino-player-value"))
    with mlflow.start_run() as run:
        mlflow.log_params(
            {
                "split_strategy": "time_based_80_20",
                "feature_count": len(features),
                "target": TARGET,
                "training_cutoff": os.getenv("TRAINING_CUTOFF_DATE", "2026-06-30"),
            }
        )
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            registered_model_name=os.getenv("MODEL_NAME", "player_value_model"),
            input_example=train_frame[features].head(3),
        )
        Path("artifacts").mkdir(exist_ok=True)
        Path("artifacts/latest_training_run.json").write_text(
            json.dumps({"run_id": run.info.run_id, "metrics": metrics}, indent=2), encoding="utf-8"
        )
    return metrics


if __name__ == "__main__":
    print(json.dumps(train(load_training_frame(os.getenv("TRAINING_DATA_PATH"))), indent=2))
