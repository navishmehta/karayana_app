"""Admin-only: seller accounts, their permissions and activity."""

from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AdminUser, DbSession
from app.core.clock import store_tz
from app.core.i18n import t
from app.core.pagination import Pagination, paginate
from app.enums.activity import ActivityAction
from app.enums.permission import Permission
from app.models import ActivityLog
from app.schemas.activity import ActivityOut
from app.schemas.common import DataResponse, MessageResponse, Page
from app.schemas.sellers import (
    CreateSellerRequest,
    PermissionGroupOut,
    PermissionOut,
    ResetSellerPasswordRequest,
    SellerOut,
    SellerPermissionsRequest,
    SellerStatusRequest,
    UpdateSellerRequest,
)
from app.services.seller_service import SellerService

router = APIRouter(prefix="/admin", tags=["admin"])

Sellers = Annotated[SellerService, Depends()]


@router.get("/permissions", response_model=DataResponse[list[PermissionGroupOut]], summary="Permission catalogue")
def permission_catalogue(_admin: AdminUser) -> DataResponse[list[PermissionGroupOut]]:
    """Permissions that can be given to sellers, grouped by module, with translated labels."""
    groups: dict[str, list[PermissionOut]] = {}
    for permission in Permission.grantable():
        groups.setdefault(permission.group, []).append(
            PermissionOut(
                key=permission.value, label=permission.label, depends_on=[d.value for d in permission.depends_on]
            )
        )
    return DataResponse(
        data=[PermissionGroupOut(key=g, label=t(f"permission_groups.{g}"), permissions=p) for g, p in groups.items()]
    )


@router.get("/sellers", response_model=Page[SellerOut], summary="List sellers")
def list_sellers(
    admin: AdminUser,
    sellers: Sellers,
    db: DbSession,
    pagination: Pagination,
    search: Annotated[str | None, Query(max_length=100)] = None,
    is_active: bool | None = None,
) -> Page[SellerOut]:
    stmt = sellers.list_query(admin, search, is_active)
    return paginate(db, stmt, pagination, lambda u: SellerOut.from_user(u, sellers.active_sessions(u.id)))


@router.post("/sellers", status_code=status.HTTP_201_CREATED, response_model=DataResponse[SellerOut])
def create_seller(body: CreateSellerRequest, admin: AdminUser, sellers: Sellers) -> DataResponse[SellerOut]:
    data = body.model_dump(exclude={"permissions", "password_confirmation"})
    seller = sellers.create(admin, data, body.permissions)
    return DataResponse(data=SellerOut.from_user(seller))


@router.get("/sellers/{seller_id}", response_model=DataResponse[SellerOut])
def get_seller(seller_id: int, admin: AdminUser, sellers: Sellers) -> DataResponse[SellerOut]:
    seller = sellers.get(admin, seller_id)
    return DataResponse(data=SellerOut.from_user(seller, sellers.active_sessions(seller.id)))


@router.patch("/sellers/{seller_id}", response_model=DataResponse[SellerOut])
def update_seller(
    seller_id: int, body: UpdateSellerRequest, admin: AdminUser, sellers: Sellers
) -> DataResponse[SellerOut]:
    seller = sellers.update(admin, sellers.get(admin, seller_id), body.model_dump(exclude_unset=True))
    return DataResponse(data=SellerOut.from_user(seller))


@router.put("/sellers/{seller_id}/permissions", response_model=DataResponse[SellerOut], summary="Replace permissions")
def set_permissions(
    seller_id: int, body: SellerPermissionsRequest, admin: AdminUser, sellers: Sellers
) -> DataResponse[SellerOut]:
    seller = sellers.set_permissions(admin, sellers.get(admin, seller_id), body.permissions)
    return DataResponse(data=SellerOut.from_user(seller))


@router.patch("/sellers/{seller_id}/status", response_model=DataResponse[SellerOut], summary="Activate / deactivate")
def set_status(
    seller_id: int, body: SellerStatusRequest, admin: AdminUser, sellers: Sellers
) -> DataResponse[SellerOut]:
    seller = sellers.set_active(admin, sellers.get(admin, seller_id), body.is_active)
    return DataResponse(data=SellerOut.from_user(seller))


@router.post("/sellers/{seller_id}/reset-password", response_model=MessageResponse)
def reset_seller_password(
    seller_id: int, body: ResetSellerPasswordRequest, admin: AdminUser, sellers: Sellers
) -> MessageResponse:
    sellers.reset_password(admin, sellers.get(admin, seller_id), body.password)
    return MessageResponse(message=t("messages.seller_password_reset"))


@router.delete("/sellers/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seller(seller_id: int, admin: AdminUser, sellers: Sellers) -> Response:
    sellers.delete(admin, sellers.get(admin, seller_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _activity_query(
    admin: AdminUser,
    user_id: int | None,
    action: ActivityAction | None,
    group: str | None,
    date_from: date | None,
    date_to: date | None,
):
    """Dates are store-local days (IST), converted to UTC for the query."""
    stmt = (
        select(ActivityLog)
        .options(selectinload(ActivityLog.user))
        .where(ActivityLog.store_id == admin.store_id)
        .order_by(ActivityLog.id.desc())
    )
    if user_id:
        stmt = stmt.where(ActivityLog.user_id == user_id)
    if action:
        stmt = stmt.where(ActivityLog.action == action.value)
    if group:
        stmt = stmt.where(ActivityLog.action.like(f"{group}.%"))
    if date_from:
        stmt = stmt.where(ActivityLog.created_at >= _utc_start_of(date_from))
    if date_to:
        stmt = stmt.where(ActivityLog.created_at < _utc_start_of(date_to + timedelta(days=1)))
    return stmt


def _utc_start_of(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=store_tz()).astimezone(UTC).replace(tzinfo=None)


@router.get("/activity-logs", response_model=Page[ActivityOut], summary="Activity log (filterable)")
def activity_logs(
    admin: AdminUser,
    db: DbSession,
    pagination: Pagination,
    user_id: int | None = None,
    action: ActivityAction | None = None,
    group: Annotated[str | None, Query(max_length=30, pattern=r"^[a-z_]+$")] = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Page[ActivityOut]:
    stmt = _activity_query(admin, user_id, action, group, date_from, date_to)
    return paginate(db, stmt, pagination, ActivityOut.from_model)


@router.get("/sellers/{seller_id}/activity", response_model=Page[ActivityOut], summary="What a seller did")
def seller_activity(
    seller_id: int, admin: AdminUser, sellers: Sellers, db: DbSession, pagination: Pagination
) -> Page[ActivityOut]:
    seller = sellers.get(admin, seller_id)
    return paginate(db, _activity_query(admin, seller.id, None, None, None, None), pagination, ActivityOut.from_model)
