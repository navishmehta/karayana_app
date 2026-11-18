from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import require
from app.core.constants import DASHBOARD_CHART_DAYS
from app.core.errors import field_error
from app.enums.permission import Permission
from app.models import User
from app.schemas.common import DataResponse
from app.schemas.dashboard import DashboardOut
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "",
    response_model=DataResponse[DashboardOut],
    response_model_exclude_unset=True,
    summary="Staff home numbers",
)
def dashboard(
    user: Annotated[User, Depends(require(Permission.DASHBOARD_VIEW))],
    service: Annotated[DashboardService, Depends()],
    days: int = DASHBOARD_CHART_DAYS[0],
) -> DataResponse[DashboardOut]:
    """Totals, values, charts and recent activity. Each block appears only with its permission
    (stock.view, expiry.view, pricing.view_purchase / view_selling, products.view; sellers count: admin).
    `days` is the stock movement chart length: 7 or 30."""
    if days not in DASHBOARD_CHART_DAYS:
        raise field_error("days", "validation.enum", attribute="days")
    return DataResponse(data=DashboardOut.for_user(service.build(user, days), user))
