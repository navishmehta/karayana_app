from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status

from app.api.deps import DbSession, require
from app.core.constants import MAX_SEARCH_LENGTH
from app.core.pagination import Pagination, paginate_rows
from app.enums.catalogue import CategorySort
from app.enums.permission import Permission
from app.models import User
from app.schemas.catalogue import CategoryCreate, CategoryOut, CategoryReorder, CategoryUpdate
from app.schemas.common import DataResponse, Page
from app.services.catalogue.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])

Categories = Annotated[CategoryService, Depends()]
CanView = Annotated[User, Depends(require(Permission.CATEGORIES_VIEW))]
CanCreate = Annotated[User, Depends(require(Permission.CATEGORIES_CREATE))]
CanUpdate = Annotated[User, Depends(require(Permission.CATEGORIES_UPDATE))]
CanDelete = Annotated[User, Depends(require(Permission.CATEGORIES_DELETE))]


@router.get("", response_model=Page[CategoryOut], summary="List categories")
def list_categories(
    user: CanView,
    categories: Categories,
    db: DbSession,
    pagination: Pagination,
    search: Annotated[str | None, Query(max_length=MAX_SEARCH_LENGTH)] = None,
    is_active: bool | None = None,
    sort: CategorySort = CategorySort.POSITION,
) -> Page[CategoryOut]:
    stmt = categories.list_query(user, search, is_active, sort)
    return paginate_rows(db, stmt, pagination, lambda row: CategoryOut.from_model(row[0], row[1]))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DataResponse[CategoryOut])
def create_category(body: CategoryCreate, user: CanCreate, categories: Categories) -> DataResponse[CategoryOut]:
    return DataResponse(data=CategoryOut.from_model(categories.create(user, body.model_dump())))


@router.patch("/reorder", status_code=status.HTTP_204_NO_CONTENT, summary="Save a new display order")
def reorder_categories(body: CategoryReorder, user: CanUpdate, categories: Categories) -> Response:
    categories.reorder(user, body.ids)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{category_id}", response_model=DataResponse[CategoryOut])
def get_category(category_id: int, user: CanView, categories: Categories) -> DataResponse[CategoryOut]:
    category = categories.get(user, category_id)
    return DataResponse(data=CategoryOut.from_model(category, categories.products_count(category)))


@router.patch("/{category_id}", response_model=DataResponse[CategoryOut])
def update_category(
    category_id: int, body: CategoryUpdate, user: CanUpdate, categories: Categories
) -> DataResponse[CategoryOut]:
    category = categories.update(user, categories.get(user, category_id), body.model_dump(exclude_unset=True))
    return DataResponse(data=CategoryOut.from_model(category, categories.products_count(category)))


@router.post("/{category_id}/image", response_model=DataResponse[CategoryOut], summary="Upload / replace image")
def upload_category_image(
    category_id: int, user: CanUpdate, categories: Categories, image: Annotated[UploadFile, File()]
) -> DataResponse[CategoryOut]:
    category = categories.replace_image(user, categories.get(user, category_id), image)
    return DataResponse(data=CategoryOut.from_model(category, categories.products_count(category)))


@router.delete("/{category_id}/image", response_model=DataResponse[CategoryOut])
def delete_category_image(category_id: int, user: CanUpdate, categories: Categories) -> DataResponse[CategoryOut]:
    category = categories.remove_image(user, categories.get(user, category_id))
    return DataResponse(data=CategoryOut.from_model(category, categories.products_count(category)))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete (only if empty)")
def delete_category(category_id: int, user: CanDelete, categories: Categories) -> Response:
    categories.delete(user, categories.get(user, category_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
