"""Brands and units used by the product form."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, DbSession, require
from app.core.constants import MAX_SEARCH_LENGTH
from app.core.errors import AppError
from app.core.pagination import Pagination, paginate
from app.enums.error_code import ErrorCode
from app.enums.permission import Permission
from app.models import User
from app.schemas.catalogue import BrandCreate, BrandOut, UnitOut
from app.schemas.common import DataResponse, Page
from app.services.catalogue.brand_unit_service import BrandService, UnitService

router = APIRouter(tags=["brands & units"])

CanView = Annotated[User, Depends(require(Permission.PRODUCTS_VIEW))]


@router.get("/units", response_model=DataResponse[list[UnitOut]], summary="Units (kg, pcs, …)")
def list_units(
    _user: CanView, units: Annotated[UnitService, Depends()], active_only: bool = False
) -> DataResponse[list[UnitOut]]:
    return DataResponse(data=[UnitOut.from_model(u) for u in units.list(active_only)])


@router.get("/brands", response_model=Page[BrandOut], summary="Brands (search for autocomplete)")
def list_brands(
    user: CanView,
    brands: Annotated[BrandService, Depends()],
    db: DbSession,
    pagination: Pagination,
    search: Annotated[str | None, Query(max_length=MAX_SEARCH_LENGTH)] = None,
) -> Page[BrandOut]:
    return paginate(db, brands.list_query(user, search), pagination, BrandOut.from_model)


@router.post("/brands", status_code=status.HTTP_201_CREATED, response_model=DataResponse[BrandOut])
def create_brand(
    body: BrandCreate, user: CurrentUser, brands: Annotated[BrandService, Depends()]
) -> DataResponse[BrandOut]:
    """Whoever can add or edit products can add a brand from the product form."""
    if not (user.has_permission(Permission.PRODUCTS_CREATE) or user.has_permission(Permission.PRODUCTS_UPDATE)):
        raise AppError(ErrorCode.FORBIDDEN)
    return DataResponse(data=BrandOut.from_model(brands.create(user, body.model_dump())))
