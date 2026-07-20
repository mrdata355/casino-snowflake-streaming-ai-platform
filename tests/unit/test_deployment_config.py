from __future__ import annotations

import os

import pytest

from scripts.apply_snowflake import configure_environment

CONFIGURATION_NAMES = [
    "PLATFORM_PREFIX",
    "ENVIRONMENT",
    "DATABASE_NAME",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_SCHEMA",
    "RESOURCE_MONITOR",
    "MONTHLY_CREDIT_QUOTA",
    "DATA_RETENTION_DAYS",
    "ADMIN_WAREHOUSE",
    "INGEST_WAREHOUSE",
    "TRANSFORM_WAREHOUSE",
    "FEATURE_WAREHOUSE",
    "CORTEX_WAREHOUSE",
    "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_ROLE",
    "ADMIN_WAREHOUSE_SIZE",
    "INGEST_WAREHOUSE_SIZE",
    "TRANSFORM_WAREHOUSE_SIZE",
    "FEATURE_WAREHOUSE_SIZE",
    "CORTEX_WAREHOUSE_SIZE",
]


def clear_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in CONFIGURATION_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_configure_dev_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_configuration(monkeypatch)

    configuration = configure_environment("dev")

    assert configuration["ENVIRONMENT"] == "DEV"
    assert configuration["DATABASE_NAME"] == "CASINO_DEV"
    assert configuration["INGEST_WAREHOUSE"] == "CASINO_DEV_INGEST_WH"
    assert configuration["MONTHLY_CREDIT_QUOTA"] == "25"
    assert configuration["DATA_RETENTION_DAYS"] == "1"


def test_configure_prod_uses_larger_transform_compute(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_configuration(monkeypatch)

    configuration = configure_environment("PROD")

    assert configuration["DATABASE_NAME"] == "CASINO_PROD"
    assert configuration["TRANSFORM_WAREHOUSE_SIZE"] == "SMALL"
    assert configuration["FEATURE_WAREHOUSE_SIZE"] == "SMALL"
    assert configuration["DATA_RETENTION_DAYS"] == "7"


def test_explicit_environment_overrides_are_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_configuration(monkeypatch)
    monkeypatch.setenv("PLATFORM_PREFIX", "PORTFOLIO")
    monkeypatch.setenv("DATABASE_NAME", "CUSTOM_QA")
    monkeypatch.setenv("MONTHLY_CREDIT_QUOTA", "99")

    configuration = configure_environment("qa")

    assert configuration["DATABASE_NAME"] == "CUSTOM_QA"
    assert configuration["MONTHLY_CREDIT_QUOTA"] == "99"
    assert os.environ["INGEST_WAREHOUSE"] == "PORTFOLIO_QA_INGEST_WH"


def test_invalid_environment_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_configuration(monkeypatch)

    with pytest.raises(ValueError, match="DEV, PROD, QA"):
        configure_environment("sandbox")
