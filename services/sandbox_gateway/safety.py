from __future__ import annotations

import re


class SandboxPolicyError(ValueError):
    pass


FORBIDDEN_SQL = [
    r"\balter\s+account\b",
    r"\bcreate\s+(user|account)\b",
    r"\bdrop\s+(account|user)\b",
    r"\bgrant\s+ownership\b",
    r"\brevoke\s+ownership\b",
    r"\bexecute\s+as\s+login\b",
    r"\bxp_cmdshell\b",
    r"\bsp_configure\b",
    r"\bshutdown\b",
    r"\bkill\s+\d+\b",
    r"\bput\s+file\b",
    r"\bget\s+@",
]

ADMIN_SQL = [
    r"\bcreate\s+(warehouse|role|resource\s+monitor|catalog|database)\b",
    r"\balter\s+(warehouse|role|resource\s+monitor|catalog|database)\b",
    r"\bdrop\s+(warehouse|role|resource\s+monitor|catalog|database)\b",
    r"\bgrant\b",
    r"\brevoke\b",
]

FORBIDDEN_PYTHON = [
    "subprocess",
    "os.system",
    "os.popen",
    "socket.",
    "requests.",
    "urllib.request",
    "dbutils.secrets",
    "%sh",
    "!pip",
    "!curl",
    "!wget",
]


def split_sql(script: str) -> list[str]:
    """Split ordinary SQL statements while respecting simple quoted strings."""
    parts: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(script):
        ch = script[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                if i + 1 < len(script) and script[i + 1] == quote:
                    buf.append(script[i + 1])
                    i += 1
                else:
                    quote = None
        elif ch in ("'", '"'):
            quote = ch
            buf.append(ch)
        elif ch == ";":
            statement = "".join(buf).strip()
            if statement:
                parts.append(statement)
            buf = []
        else:
            buf.append(ch)
        i += 1
    statement = "".join(buf).strip()
    if statement:
        parts.append(statement)
    return parts


def _matches(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.I | re.S) for pattern in patterns)


def validate_sql(script: str, *, admin_lab: bool) -> list[str]:
    statements = split_sql(script)
    if not statements:
        raise SandboxPolicyError("No executable SQL statement was supplied.")
    if len(statements) > 20:
        raise SandboxPolicyError("A sandbox execution is limited to 20 SQL statements.")
    for statement in statements:
        if len(statement) > 50_000:
            raise SandboxPolicyError("A single SQL statement exceeds the sandbox size limit.")
        if _matches(FORBIDDEN_SQL, statement):
            raise SandboxPolicyError("The statement contains an operation forbidden in OpsReady sandboxes.")
        if not admin_lab and _matches(ADMIN_SQL, statement):
            raise SandboxPolicyError(
                "This is an account/admin-level operation. Create an admin-lab session in a dedicated training account to run it."
            )
    return statements


def validate_python(code: str) -> None:
    lowered = code.lower()
    for token in FORBIDDEN_PYTHON:
        if token.lower() in lowered:
            raise SandboxPolicyError(f"Python token '{token}' is blocked in the bounded Databricks execution profile.")
    if len(code) > 50_000:
        raise SandboxPolicyError("Python command exceeds the sandbox size limit.")
