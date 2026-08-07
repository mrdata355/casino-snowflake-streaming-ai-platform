from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Platform = Literal["snowflake", "databricks", "sqlserver"]
Language = Literal["sql", "python"]


class CreateSessionRequest(BaseModel):
    platform: Platform
    admin_lab: bool = False


class SessionInfo(BaseModel):
    session_id: str
    platform: Platform
    namespace: str
    admin_lab: bool
    expires_in_minutes: int = 60


class ExecuteRequest(BaseModel):
    session_id: str
    task_id: str = Field(min_length=1, max_length=120)
    code: str = Field(min_length=1, max_length=100_000)
    language: Language = "sql"


class ExecuteResult(BaseModel):
    ok: bool
    platform: Platform
    session_id: str
    task_id: str
    language: Language
    state: str
    columns: list[str] = []
    rows: list[list[object]] = []
    message: str = ""
    statement_id: str | None = None
    elapsed_ms: int | None = None
    validated: bool = False
    validation: dict[str, object] = {}


class Capability(BaseModel):
    platform: Platform
    available: bool
    sql: bool
    python: bool = False
    admin_labs: bool = False
    note: str = ""
