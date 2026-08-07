from __future__ import annotations

import os
import re
import secrets
import time
from contextlib import suppress
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .adapters import DatabricksAdapter, SnowflakeAdapter, SqlServerAdapter
from .models import (
    Capability,
    CreateSessionRequest,
    ExecuteRequest,
    ExecuteResult,
    SessionInfo,
)
from .safety import SandboxPolicyError

app = FastAPI(title="OpsReady Sandbox Gateway", version="1.0.0")

DEFAULT_CORS = (
    "http://localhost:3000,http://localhost:8080,http://127.0.0.1:5500,"
    "https://casino-snowflake-streaming-ai-platf-five.vercel.app"
)
origins = [
    item.strip()
    for item in os.getenv("OPSREADY_CORS_ORIGINS", DEFAULT_CORS).split(",")
    if item.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

snowflake = SnowflakeAdapter()
databricks = DatabricksAdapter()
sqlserver = SqlServerAdapter()
ADAPTERS = {
    "snowflake": snowflake,
    "databricks": databricks,
    "sqlserver": sqlserver,
}
SESSION_TTL = int(os.getenv("OPSREADY_SESSION_TTL_MINUTES", "60")) * 60


@dataclass
class Session:
    session_id: str
    platform: str
    namespace: str
    admin_lab: bool
    created_at: float


SESSIONS: dict[str, Session] = {}


def _short_id() -> str:
    return secrets.token_hex(5).upper()


def _session_namespace(platform: str, token: str) -> str:
    if platform == "sqlserver":
        return f"OpsReady_{token}"
    return f"S_{token}"


def _get_session(session_id: str) -> Session:
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(
            404,
            "Sandbox session not found or already cleaned up.",
        )
    if time.time() - session.created_at > SESSION_TTL:
        with suppress(Exception):
            ADAPTERS[session.platform].cleanup(session.namespace)
        SESSIONS.pop(session_id, None)
        raise HTTPException(
            410,
            "Sandbox session expired and cleanup was requested.",
        )
    return session


def _safe_task_id(task_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:-]", "_", task_id)[:120]


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "service": "opsready-sandbox-gateway",
        "sessions": len(SESSIONS),
    }


@app.get("/capabilities", response_model=list[Capability])
def capabilities() -> list[Capability]:
    return [
        Capability(
            platform="snowflake",
            available=snowflake.available,
            sql=True,
            python=False,
            admin_labs=snowflake.allow_admin,
            note=(
                "Real Snowflake SQL through snowflake-connector-python "
                "in an isolated training schema."
            ),
        ),
        Capability(
            platform="databricks",
            available=databricks.available,
            sql=True,
            python=databricks.python_available,
            admin_labs=databricks.allow_admin,
            note=(
                "SQL uses Statement Execution API; Python uses bounded "
                "Command Execution on a configured classic all-purpose cluster."
            ),
        ),
        Capability(
            platform="sqlserver",
            available=sqlserver.available,
            sql=True,
            python=False,
            admin_labs=sqlserver.allow_admin,
            note=(
                "Real T-SQL against an isolated SQL Server training database, "
                "intended for local/container sandbox use."
            ),
        ),
    ]


@app.post("/sessions", response_model=SessionInfo)
def create_session(req: CreateSessionRequest) -> SessionInfo:
    adapter = ADAPTERS[req.platform]
    if not adapter.available:
        raise HTTPException(
            503,
            f"{req.platform} is not configured on this gateway.",
        )
    token = _short_id()
    namespace = _session_namespace(req.platform, token)
    try:
        adapter.create_session(namespace, req.admin_lab)
    except SandboxPolicyError as exc:
        raise HTTPException(403, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            502,
            f"Failed to create {req.platform} sandbox: {exc}",
        ) from exc

    session_id = secrets.token_urlsafe(24)
    SESSIONS[session_id] = Session(
        session_id,
        req.platform,
        namespace,
        req.admin_lab,
        time.time(),
    )
    display_namespace = namespace
    if req.platform == "snowflake":
        display_namespace = f"{snowflake.database}.{namespace}"
    elif req.platform == "databricks":
        display_namespace = f"{databricks.catalog}.{namespace}"

    return SessionInfo(
        session_id=session_id,
        platform=req.platform,
        namespace=display_namespace,
        admin_lab=req.admin_lab,
        expires_in_minutes=SESSION_TTL // 60,
    )


@app.post("/execute", response_model=ExecuteResult)
def execute(req: ExecuteRequest) -> ExecuteResult:
    session = _get_session(req.session_id)
    adapter = ADAPTERS[session.platform]
    if req.language == "python" and session.platform != "databricks":
        raise HTTPException(
            400,
            "Python execution is currently supported only for Databricks sessions.",
        )

    started = time.perf_counter()
    try:
        if session.platform == "databricks":
            if req.language == "python":
                raw = databricks.execute_python(session.namespace, req.code)
            else:
                raw = databricks.execute_sql(
                    session.namespace,
                    req.code,
                    admin_lab=session.admin_lab,
                )
        else:
            raw = adapter.execute(
                session.namespace,
                req.code,
                admin_lab=session.admin_lab,
            )
    except SandboxPolicyError as exc:
        raise HTTPException(403, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Execution failed: {exc}") from exc

    elapsed = raw.elapsed_ms or int((time.perf_counter() - started) * 1000)
    return ExecuteResult(
        ok=True,
        platform=session.platform,
        session_id=session.session_id,
        task_id=_safe_task_id(req.task_id),
        language=req.language,
        state=raw.state,
        columns=raw.columns,
        rows=raw.rows,
        message=raw.message,
        statement_id=raw.statement_id,
        elapsed_ms=elapsed,
        validated=raw.state == "SUCCEEDED",
        validation={
            "isolation": True,
            "namespace": session.namespace,
            "policy_profile": (
                "admin-lab" if session.admin_lab else "schema-safe"
            ),
            "execution_succeeded": raw.state == "SUCCEEDED",
        },
    )


@app.delete("/sessions/{session_id}")
def cleanup(session_id: str) -> dict[str, object]:
    session = _get_session(session_id)
    try:
        ADAPTERS[session.platform].cleanup(session.namespace)
    except Exception as exc:
        raise HTTPException(502, f"Cleanup failed: {exc}") from exc
    finally:
        SESSIONS.pop(session_id, None)
    return {
        "ok": True,
        "session_id": session_id,
        "platform": session.platform,
        "cleaned": True,
    }
