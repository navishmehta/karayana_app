import math
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import require
from app.core.constants import DEFAULT_PER_PAGE, EXPIRY_LOOKAHEAD_MAX_DAYS, MAX_PER_PAGE
from app.enums.permission import Permission
from app.enums.report import ExportFormat, ReportType
from app.models import User
from app.schemas.common import DataResponse, PageMeta
from app.schemas.reports import ReportColumnOut, ReportInfoOut, ReportOut
from app.services.reports.base import ReportFilters
from app.services.reports.definitions import REPORTS
from app.services.reports.service import ReportService, display_value

router = APIRouter(prefix="/reports", tags=["reports"])

CanView = Annotated[User, Depends(require(Permission.REPORTS_VIEW))]
CanExport = Annotated[User, Depends(require(Permission.REPORTS_VIEW, Permission.REPORTS_EXPORT))]
Reports = Annotated[ReportService, Depends()]


def report_filters(
    category_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    within_days: Annotated[int | None, Query(ge=0, le=EXPIRY_LOOKAHEAD_MAX_DAYS)] = None,
) -> ReportFilters:
    return ReportFilters(category_id=category_id, date_from=date_from, date_to=date_to, within_days=within_days)


Filters = Annotated[ReportFilters, Depends(report_filters)]


@router.get("", response_model=DataResponse[list[ReportInfoOut]], summary="Reports this user may open")
def list_reports(user: CanView, reports: Reports) -> DataResponse[list[ReportInfoOut]]:
    can_export = user.has_permission(Permission.REPORTS_EXPORT)
    return DataResponse(
        data=[
            ReportInfoOut(
                key=kind.value,
                label=REPORTS[kind].label,
                description=REPORTS[kind].description,
                filters=list(REPORTS[kind].filters),
                can_export=can_export,
            )
            for kind in reports.available(user)
        ]
    )


@router.get("/{kind}", response_model=DataResponse[ReportOut], summary="View a report (paged)")
def view_report(
    kind: ReportType,
    user: CanView,
    reports: Reports,
    filters: Filters,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=MAX_PER_PAGE)] = DEFAULT_PER_PAGE,
) -> DataResponse[ReportOut]:
    result = reports.run(user, kind, filters)
    window = result.rows[(page - 1) * per_page : page * per_page]
    columns = result.columns
    return DataResponse(
        data=ReportOut(
            key=kind.value,
            label=REPORTS[kind].label,
            columns=[ReportColumnOut(key=c.key, label=c.label, kind=c.kind) for c in columns],
            rows=[{c.key: display_value(r[c.key], c.kind) for c in columns} for r in window],
            totals={c.key: display_value(result.totals[c.key], c.kind) for c in columns if c.key in result.totals}
            if result.totals
            else None,
            truncated=result.truncated,
            meta=PageMeta(
                page=page,
                per_page=per_page,
                total=len(result.rows),
                last_page=max(1, math.ceil(len(result.rows) / per_page)),
            ),
        )
    )


@router.get("/{kind}/export", summary="Download as CSV or Excel", response_class=Response)
def export_report(
    kind: ReportType,
    user: CanExport,
    reports: Reports,
    filters: Filters,
    format: ExportFormat = ExportFormat.XLSX,  # noqa: A002
) -> Response:
    content, filename = reports.export(user, kind, filters, format)
    return Response(
        content=content,
        media_type=format.media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store"},
    )
