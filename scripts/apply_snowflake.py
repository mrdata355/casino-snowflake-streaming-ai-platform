from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from services.common.snowflake import connection

TOKEN_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")
SUPPORTED_ENVIRONMENTS = {"DEV", "QA", "PROD"}
ENVIRONMENT_DEFAULTS = {
    "DEV": {"credit_quota": "25", "retention_days": "1"},
    "QA": {"credit_quota": "75", "retention_days": "3"},
    "PROD": {"credit_quota": "250", "retention_days": "7"},
}


def set_if_missing(name: str, value: str) -> None:
    if not os.getenv(name):
        os.environ[name] = value


def configure_environment(environment: str) -> dict[str, str]:
    """Derive safe object names while preserving explicit environment overrides."""
    resolved_environment = environment.strip().upper()
    if resolved_environment not in SUPPORTED_ENVIRONMENTS:
        supported = ", ".join(sorted(SUPPORTED_ENVIRONMENTS))
        raise ValueError(f"environment must be one of: {supported}")

    prefix = (os.getenv("PLATFORM_PREFIX") or "CASINO").strip().upper()
    database = (
        os.getenv("DATABASE_NAME")
        or os.getenv("SNOWFLAKE_DATABASE")
        or f"{prefix}_{resolved_environment}"
    ).strip().upper()
    defaults = ENVIRONMENT_DEFAULTS[resolved_environment]

    derived = {
        "PLATFORM_PREFIX": prefix,
        "ENVIRONMENT": resolved_environment,
        "DATABASE_NAME": database,
        "SNOWFLAKE_DATABASE": database,
        "SNOWFLAKE_SCHEMA": "OPS",
        "RESOURCE_MONITOR": f"{prefix}_{resolved_environment}_MONTHLY_RM",
        "MONTHLY_CREDIT_QUOTA": defaults["credit_quota"],
        "DATA_RETENTION_DAYS": defaults["retention_days"],
        "ADMIN_WAREHOUSE": f"{prefix}_{resolved_environment}_ADMIN_WH",
        "INGEST_WAREHOUSE": f"{prefix}_{resolved_environment}_INGEST_WH",
        "TRANSFORM_WAREHOUSE": f"{prefix}_{resolved_environment}_TRANSFORM_WH",
        "FEATURE_WAREHOUSE": f"{prefix}_{resolved_environment}_FEATURE_WH",
        "CORTEX_WAREHOUSE": f"{prefix}_{resolved_environment}_CORTEX_WH",
        "SNOWFLAKE_WAREHOUSE": f"{prefix}_{resolved_environment}_ADMIN_WH",
        "SNOWFLAKE_ROLE": "SYSADMIN",
        "ADMIN_WAREHOUSE_SIZE": "XSMALL",
        "INGEST_WAREHOUSE_SIZE": "XSMALL",
        "TRANSFORM_WAREHOUSE_SIZE": "SMALL" if resolved_environment == "PROD" else "XSMALL",
        "FEATURE_WAREHOUSE_SIZE": "SMALL" if resolved_environment == "PROD" else "XSMALL",
        "CORTEX_WAREHOUSE_SIZE": "XSMALL",
    }
    for name, value in derived.items():
        set_if_missing(name, value)

    account = os.getenv("SNOWFLAKE_ACCOUNT_IDENTIFIER") or os.getenv("SNOWFLAKE_ACCOUNT")
    if account:
        set_if_missing("SNOWFLAKE_ACCOUNT_IDENTIFIER", account)

    return {name: os.environ[name] for name in derived}


def render_environment_tokens(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        value = os.getenv(name)
        if value is None:
            raise RuntimeError(f"Missing environment variable required by template: {name}")
        return value

    return TOKEN_PATTERN.sub(replace, text)


def ordered_paths(directory: str | None, file_path: str | None) -> list[Path]:
    if bool(directory) == bool(file_path):
        raise ValueError("Provide exactly one of directory or file_path")
    if file_path:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        return [path]
    paths = sorted(Path(directory or "").glob("*.sql"))
    if not paths:
        raise FileNotFoundError(f"No SQL files found in {directory}")
    return paths


def apply(directory: str | None, file_path: str | None, dry_run: bool) -> None:
    paths = ordered_paths(directory, file_path)
    rendered = [(path, render_environment_tokens(path.read_text(encoding="utf-8"))) for path in paths]
    if dry_run:
        for path, sql in rendered:
            print(f"DRY RUN {path}: {len(sql)} characters")
        return

    with connection("deployment.apply_snowflake") as conn:
        for path, sql in rendered:
            print(f"APPLY {path}")
            for cursor in conn.execute_stream(sql):
                cursor.close()
        conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply ordered Snowflake SQL templates")
    parser.add_argument(
        "--environment",
        default=os.getenv("DEPLOY_ENV", "DEV"),
        choices=["dev", "qa", "prod", "DEV", "QA", "PROD"],
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--directory", default=None)
    group.add_argument("--file", dest="file_path", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    configuration = configure_environment(args.environment)
    print(
        "DEPLOYMENT TARGET: "
        f"environment={configuration['ENVIRONMENT']} "
        f"database={configuration['DATABASE_NAME']} "
        f"dry_run={args.dry_run}"
    )
    apply(args.directory or (None if args.file_path else "snowflake/ddl"), args.file_path, args.dry_run)


if __name__ == "__main__":
    main()
