"""Схеми відповідей трекера: спільні для MCP-сервера (output_schema) і агента (перевірка відповіді клієнтом)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

Severity = Literal["critical", "high", "medium", "low"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReleaseOut(Strict):
    version: str
    status: Literal["released", "in_testing", "planned"]
    release_date: str | None
    solution: str | None
    deployed_to: list[str]


class DefectOut(Strict):
    id: str
    title: str
    version: str
    severity: Severity
    status: Literal["open", "resolved"]
    component: str
    environment: str
    fixed_in: str | None


class DefectListOut(Strict):
    team: str
    count: int
    defects: list[DefectOut]


class TicketOut(Strict):
    ticket_id: str
    status: Literal["created", "already_exists"]
    idempotency_key: str
