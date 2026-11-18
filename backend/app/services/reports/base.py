"""Report building blocks: columns (each may need a permission), filters, and the report definition."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.i18n import t
from app.enums.permission import Permission
from app.enums.report import ColumnKind, ReportType
from app.models import User


@dataclass(frozen=True)
class Column:
    key: str
    kind: ColumnKind
    permission: Permission | None = None  # column is left out entirely without it
    total: bool = False  # summed in the totals row

    @property
    def label(self) -> str:
        return t(f"reports.columns.{self.key}")


@dataclass
class ReportFilters:
    category_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    within_days: int | None = None


Row = dict[str, Any]
RowBuilder = Callable[[Session, User, ReportFilters], Iterable[Row]]


@dataclass(frozen=True)
class ReportDefinition:
    type: ReportType
    permissions: tuple[Permission, ...]  # needed on top of reports.view
    columns: tuple[Column, ...]
    build: RowBuilder
    filters: tuple[str, ...] = field(default=("category_id",))

    @property
    def label(self) -> str:
        return t(f"reports.types.{self.type.value}.label")

    @property
    def description(self) -> str:
        return t(f"reports.types.{self.type.value}.description")

    def allowed(self, user: User) -> bool:
        return user.has_permission(Permission.REPORTS_VIEW) and all(user.has_permission(p) for p in self.permissions)

    def visible_columns(self, user: User) -> list[Column]:
        return [c for c in self.columns if c.permission is None or user.has_permission(c.permission)]


@dataclass
class ReportResult:
    columns: list[Column]
    rows: list[Row]  # only visible columns
    totals: Row | None
    truncated: bool


def only_visible(row: Row, columns: list[Column]) -> Row:
    return {c.key: row.get(c.key) for c in columns}


def totals_for(rows: list[Row], columns: list[Column]) -> Row | None:
    summed = [c for c in columns if c.total]
    if not summed:
        return None
    return {c.key: sum((Decimal(r[c.key]) for r in rows if r.get(c.key) is not None), Decimal(0)) for c in summed}
