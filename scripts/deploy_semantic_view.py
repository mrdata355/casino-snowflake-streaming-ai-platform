from __future__ import annotations

import argparse
import os
from pathlib import Path

from scripts.apply_snowflake import render_environment_tokens
from services.common.snowflake import connection


def deploy(yaml_path: str, schema: str, verify_only: bool) -> None:
    yaml_text = render_environment_tokens(Path(yaml_path).read_text(encoding="utf-8"))
    with connection("deployment.semantic_view") as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(%s, %s, %s)",
                (schema, yaml_text, verify_only),
            )
            print(cur.fetchone()[0])
        finally:
            cur.close()


def main() -> None:
    database = os.getenv("SNOWFLAKE_DATABASE", os.getenv("DATABASE_NAME", "CASINO_DEV"))
    parser = argparse.ArgumentParser(description="Verify or deploy a Snowflake semantic view")
    parser.add_argument("--yaml", required=True)
    parser.add_argument("--schema", default=f"{database}.SEMANTIC")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    deploy(args.yaml, args.schema, verify_only=not args.apply)


if __name__ == "__main__":
    main()
