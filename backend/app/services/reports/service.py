"""Run a report for a user, and turn it into CSV or Excel."""

import csv
import io
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from app.api.deps import DbSession
from app.core.clock import format_display_date, store_today, to_store_time
from app.core.constants import CSV_ENCODING, REPORT_MAX_ROWS, XLSX_MAX_COLUMN_WIDTH
from app.core.errors import AppError
from app.core.i18n import t
from app.core.money import money, quantity
from app.enums.activity import ActivityAction
from app.enums.error_code import ErrorCode
from app.enums.permission import Permission
from app.enums.report import ColumnKind, ExportFormat, ReportType
from app.models import User
from app.services.audit import Audit

from .base import Column, ReportFilters, ReportResult, only_visible, totals_for
from .definitions import REPORTS

XLSX_NUMBER_FORMATS = {
    ColumnKind.MONEY: "#,##0.00",
    ColumnKind.QUANTITY: "#,##0.###",
    ColumnKind.PERCENT: '0.00"%"',
    ColumnKind.INT: "0",
    ColumnKind.DATE: "DD-MM-YYYY",
    ColumnKind.DATETIME: "DD-MM-YYYY HH:MM",
}


class ReportService:
    def __init__(self, db: DbSession, audit: Audit) -> None:
        self.db = db
        self.audit = audit

    def available(self, user: User) -> list[ReportType]:
        return [kind for kind, definition in REPORTS.items() if definition.allowed(user)]

    def run(self, user: User, kind: ReportType, filters: ReportFilters) -> ReportResult:
        definition = REPORTS[kind]
        if not definition.allowed(user):
            raise AppError(ErrorCode.FORBIDDEN)
        columns = definition.visible_columns(user)
        rows = [only_visible(row, columns) for row in definition.build(self.db, user, filters)]
        truncated = len(rows) > REPORT_MAX_ROWS
        rows = rows[:REPORT_MAX_ROWS]
        return ReportResult(columns=columns, rows=rows, totals=totals_for(rows, columns), truncated=truncated)

    def export(self, user: User, kind: ReportType, filters: ReportFilters, fmt: ExportFormat) -> tuple[bytes, str]:
        if not user.has_permission(Permission.REPORTS_EXPORT):
            raise AppError(ErrorCode.FORBIDDEN)
        result = self.run(user, kind, filters)
        content = _to_csv(result) if fmt == ExportFormat.CSV else _to_xlsx(result, REPORTS[kind].label)
        filename = f"{kind.value}-{store_today().strftime('%d-%m-%Y')}.{fmt.value}"
        self.audit.record(
            ActivityAction.REPORT_EXPORTED,
            actor=user,
            properties={"report": kind.value, "format": fmt.value, "rows": len(result.rows)},
        )
        self.db.commit()
        return content, filename


# --- Formatting -----------------------------------------------------------------------------------


def display_value(value: Any, kind: ColumnKind) -> str:
    """Text for CSV and the in-app table: DD-MM-YYYY dates, 2-decimal money, trimmed quantities."""
    if value is None:
        return ""
    match kind:
        case ColumnKind.MONEY | ColumnKind.PERCENT:
            return str(money(value))
        case ColumnKind.QUANTITY:
            return _trim(quantity(value))
        case ColumnKind.DATE:
            return format_display_date(value) or ""
        case ColumnKind.DATETIME:
            local = to_store_time(value)
            return local.strftime("%d-%m-%Y %H:%M") if local else ""
        case _:
            return str(value)


def _trim(value: Decimal) -> str:
    text = f"{value:f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def _to_csv(result: ReportResult) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([c.label for c in result.columns])
    for row in result.rows:
        writer.writerow([display_value(row[c.key], c.kind) for c in result.columns])
    if result.totals:
        writer.writerow(_totals_line(result.columns, result.totals, display_value))
    return buffer.getvalue().encode(CSV_ENCODING)


def _xlsx_value(value: Any, kind: ColumnKind) -> Any:
    if value is None:
        return None
    if kind in (ColumnKind.MONEY, ColumnKind.PERCENT, ColumnKind.QUANTITY):
        return float(value)  # Excel cells are binary floats; display format keeps 2/3 decimals
    if kind == ColumnKind.DATETIME and isinstance(value, datetime):
        local = to_store_time(value)
        return local.replace(tzinfo=None) if local else None
    if kind == ColumnKind.DATE and isinstance(value, date):
        return value
    return value


def _to_xlsx(result: ReportResult, title: str) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = title[:31]  # Excel limit
    sheet.append([c.label for c in result.columns])
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in result.rows:
        sheet.append([_xlsx_value(row[c.key], c.kind) for c in result.columns])
    if result.totals:
        sheet.append(_totals_line(result.columns, result.totals, _xlsx_value))
        for cell in sheet[sheet.max_row]:
            cell.font = Font(bold=True)
    for index, column in enumerate(result.columns, start=1):
        letter = get_column_letter(index)
        if column.kind in XLSX_NUMBER_FORMATS:
            for (cell,) in sheet.iter_rows(min_row=2, min_col=index, max_col=index):
                cell.number_format = XLSX_NUMBER_FORMATS[column.kind]
        longest = max([len(column.label), *(len(display_value(r[column.key], column.kind)) for r in result.rows)])
        sheet.column_dimensions[letter].width = min(longest + 2, XLSX_MAX_COLUMN_WIDTH)
    sheet.freeze_panes = "A2"
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _totals_line(columns: list[Column], totals: dict, fmt) -> list:
    line = [fmt(totals[c.key], c.kind) if c.key in totals else "" for c in columns]
    if columns[0].key not in totals:
        line[0] = t("reports.total")
    return line
