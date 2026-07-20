from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from services.common.snowflake import connection

TOKEN_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


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
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--directory", default=None)
    group.add_argument("--file", dest="file_path", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply(args.directory or (None if args.file_path else "snowflake/ddl"), args.file_path, args.dry_run)


if __name__ == "__main__":
    main()
