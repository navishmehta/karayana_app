"""Admin-only catalogue maintenance: units, brand edits, restoring deleted products."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import AdminUser
from app.schemas.catalogue import BrandOut, BrandUpdate, UnitCreate, UnitOut, UnitUpdate
from app.schemas.common import DataResponse
from app.schemas.products import ProductOut
from app.services.catalogue.brand_unit_service import BrandService, UnitService
from app.services.catalogue.product_service import ProductService

router = APIRouter(prefix="/admin", tags=["admin"])

Units = Annotated[UnitService, Depends()]
Brands = Annotated[BrandService, Depends()]


@router.post("/units", status_code=status.HTTP_201_CREATED, response_model=DataResponse[UnitOut])
def create_unit(body: UnitCreate, admin: AdminUser, units: Units) -> DataResponse[UnitOut]:
    return DataResponse(data=UnitOut.from_model(units.create(admin, body.model_dump())))


@router.patch("/units/{unit_id}", response_model=DataResponse[UnitOut])
def update_unit(unit_id: int, body: UnitUpdate, admin: AdminUser, units: Units) -> DataResponse[UnitOut]:
    unit = units.update(admin, units.get(unit_id), body.model_dump(exclude_unset=True))
    return DataResponse(data=UnitOut.from_model(unit))


@router.delete("/units/{unit_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete (only if unused)")
def delete_unit(unit_id: int, admin: AdminUser, units: Units) -> Response:
    units.delete(admin, units.get(unit_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/brands/{brand_id}", response_model=DataResponse[BrandOut])
def update_brand(brand_id: int, body: BrandUpdate, admin: AdminUser, brands: Brands) -> DataResponse[BrandOut]:
    brand = brands.update(admin, brands.get(admin, brand_id), body.model_dump(exclude_unset=True))
    return DataResponse(data=BrandOut.from_model(brand))


@router.delete("/brands/{brand_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete (only if unused)")
def delete_brand(brand_id: int, admin: AdminUser, brands: Brands) -> Response:
    brands.delete(admin, brands.get(admin, brand_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/products/{product_id}/restore", response_model=DataResponse[ProductOut], response_model_exclude_unset=True
)
def restore_product(
    product_id: int, admin: AdminUser, products: Annotated[ProductService, Depends()]
) -> DataResponse[ProductOut]:
    product = products.restore(admin, products.get(admin, product_id, with_deleted=True))
    return DataResponse(data=ProductOut.for_user(product, admin))
