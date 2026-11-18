from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status

from app.api.deps import DbSession, require
from app.core.constants import CODE_MAX_LENGTH, MAX_SEARCH_LENGTH
from app.core.pagination import Pagination, paginate
from app.enums.catalogue import ProductSort
from app.enums.permission import Permission
from app.enums.stock import StockStatus
from app.models import User
from app.schemas.common import DataResponse, Page
from app.schemas.products import ImageUpdate, ProductCreate, ProductOut, ProductUpdate
from app.services.catalogue.product_service import ProductFilters, ProductService, product_query

router = APIRouter(prefix="/products", tags=["products"])

Products = Annotated[ProductService, Depends()]
CanView = Annotated[User, Depends(require(Permission.PRODUCTS_VIEW))]
CanCreate = Annotated[User, Depends(require(Permission.PRODUCTS_CREATE))]  # admin only
CanUpdate = Annotated[User, Depends(require(Permission.PRODUCTS_UPDATE))]
CanDelete = Annotated[User, Depends(require(Permission.PRODUCTS_DELETE))]

# Optional fields the user may not see are left out of the JSON entirely.
HIDE_UNSET = {"response_model_exclude_unset": True}


@router.get("", response_model=Page[ProductOut], summary="List / search / filter products", **HIDE_UNSET)
def list_products(
    user: CanView,
    db: DbSession,
    pagination: Pagination,
    search: Annotated[str | None, Query(max_length=MAX_SEARCH_LENGTH)] = None,
    category_id: Annotated[list[int] | None, Query()] = None,
    brand_id: Annotated[list[int] | None, Query()] = None,
    min_price: Annotated[Decimal | None, Query(ge=0)] = None,
    max_price: Annotated[Decimal | None, Query(ge=0)] = None,
    stock_status: StockStatus | None = None,
    is_active: bool | None = None,
    is_visible_to_customers: bool | None = None,
    is_featured: bool | None = None,
    sort: ProductSort = ProductSort.NAME_ASC,
) -> Page[ProductOut]:
    filters = ProductFilters(
        search=search,
        category_ids=category_id,
        brand_ids=brand_id,
        min_price=min_price,
        max_price=max_price,
        stock_status=stock_status,
        is_active=is_active,
        is_visible_to_customers=is_visible_to_customers,
        is_featured=is_featured,
        sort=sort,
    )
    filters.check_allowed(user)
    return paginate(db, product_query(user.store_id, filters), pagination, lambda p: ProductOut.for_user(p, user))


@router.get("/lookup", response_model=DataResponse[ProductOut], summary="Exact match by barcode or SKU", **HIDE_UNSET)
def lookup_product(
    user: CanView,
    products: Products,
    barcode: Annotated[str | None, Query(max_length=CODE_MAX_LENGTH)] = None,
    sku: Annotated[str | None, Query(max_length=CODE_MAX_LENGTH)] = None,
) -> DataResponse[ProductOut]:
    return DataResponse(data=ProductOut.for_user(products.lookup(user, barcode, sku), user))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DataResponse[ProductOut], **HIDE_UNSET)
def create_product(body: ProductCreate, user: CanCreate, products: Products) -> DataResponse[ProductOut]:
    """Admin only."""
    product = products.create(user, body.model_dump(exclude_none=True))
    return DataResponse(data=ProductOut.for_user(product, user))


@router.get("/{product_id}", response_model=DataResponse[ProductOut], **HIDE_UNSET)
def get_product(product_id: int, user: CanView, products: Products) -> DataResponse[ProductOut]:
    return DataResponse(data=ProductOut.for_user(products.get(user, product_id), user))


@router.patch("/{product_id}", response_model=DataResponse[ProductOut], **HIDE_UNSET)
def update_product(
    product_id: int, body: ProductUpdate, user: CanUpdate, products: Products
) -> DataResponse[ProductOut]:
    product = products.update(user, products.get(user, product_id), body.model_dump(exclude_unset=True))
    return DataResponse(data=ProductOut.for_user(product, user))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete (admin can restore)")
def delete_product(product_id: int, user: CanDelete, products: Products) -> Response:
    products.delete(user, products.get(user, product_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{product_id}/images",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[ProductOut],
    summary="Upload an image",
    **HIDE_UNSET,
)
def upload_product_image(
    product_id: int, user: CanUpdate, products: Products, image: Annotated[UploadFile, File()]
) -> DataResponse[ProductOut]:
    product = products.get(user, product_id)
    products.add_image(user, product, image)
    return DataResponse(data=ProductOut.for_user(products.get(user, product_id), user))


@router.patch(
    "/{product_id}/images/{image_id}",
    response_model=DataResponse[ProductOut],
    summary="Make main image / reorder",
    **HIDE_UNSET,
)
def update_product_image(
    product_id: int, image_id: int, body: ImageUpdate, user: CanUpdate, products: Products
) -> DataResponse[ProductOut]:
    product = products.get(user, product_id)
    product = products.update_image(product, products.get_image(product, image_id), body.model_dump(exclude_unset=True))
    return DataResponse(data=ProductOut.for_user(product, user))


@router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_image(product_id: int, image_id: int, user: CanUpdate, products: Products) -> Response:
    product = products.get(user, product_id)
    products.delete_image(user, product, products.get_image(product, image_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
