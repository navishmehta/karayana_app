from typing import Any

from pydantic import BaseModel

from app.enums.report import ColumnKind
from app.schemas.common import PageMeta


class ReportInfoOut(BaseModel):
    key: str
    label: str
    description: str
    filters: list[str]
    can_export: bool


class ReportColumnOut(BaseModel):
    key: str
    label: str
    kind: ColumnKind


class ReportOut(BaseModel):
    """Values are display strings (DD-MM-YYYY dates, 2-decimal money) so every client shows them the same way."""

    key: str
    label: str
    columns: list[ReportColumnOut]
    rows: list[dict[str, Any]]
    totals: dict[str, Any] | None
    truncated: bool
    meta: PageMeta
