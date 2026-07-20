#!/usr/bin/env bash
set -euo pipefail

python -m scripts.validate_env
python - <<'PY'
from services.common.snowflake import connection

with connection() as conn:
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT CURRENT_ACCOUNT(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE()")
        print(cursor.fetchone())
        cursor.execute("SELECT COUNT(*) FROM IDENTIFIER(%s)", (f"{__import__('os').environ['SNOWFLAKE_DATABASE']}.OPS.PLATFORM_HEALTH",))
        print({"platform_health_rows": cursor.fetchone()[0]})
    finally:
        cursor.close()
PY
