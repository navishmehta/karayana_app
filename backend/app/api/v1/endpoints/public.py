"""Customer catalogue: no login. Rate-limited per IP and cacheable for a short time."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import DbSession
from app.core.constants import MAX_SEARCH_LENGTH, PUBLIC_CACHE_SECONDS, PUBLIC_HIGHLIGHT_LIMIT, PUBLIC_MAX_PER_PAGE
from app.core.pagination import paginate
from app.core.rate_limit import RateLimitRule, rate_limiter
from app.schemas.common import DataResponse, Page, PageParams
from app.schemas.public import PublicCategoryOut, PublicProductOut, PublicStoreOut
from app.services.catalogue.public_catalogue import PublicCatalogue, PublicFilters, PublicSort


def public_request(request: Request, response: Response) -> None:
    """Applied to every public route: per-IP rate limit, and let browsers/CDNs cache briefly."""
    rate_limiter.hit(RateLimitRule.PUBLIC, request.client.host if request.client else "unknown")
    response.headers["Cache-Control"] = f"public, max-age={PUBLIC_CACHE_SECONDS}"


router = APIRouter(prefix="/public", tags=["public catalogue"], dependencies=[Depends(public_request)])

Catalogue = Annotated[PublicCatalogue, Depends()]


def public_page(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=PUBLIC_MAX_PER_PAGE)] = 20,
) -> PageParams:
    return PageParams(page=page, per_page=per_page)


PublicPagination = Annotated[PageParams, Depends(public_page)]


@router.get("/store", response_model=DataResponse[PublicStoreOut], summary="Store name, logo and contact details")
def store_info(catalogue: Catalogue) -> DataResponse[PublicStoreOut]:
    return DataResponse(data=PublicStoreOut.build(catalogue.store, catalogue.settings))


@router.get("/categories", response_model=DataResponse[list[PublicCategoryOut]], summary="Categories with products")
def categories(catalogue: Catalogue) -> DataResponse[list[PublicCategoryOut]]:
    return DataResponse(data=[PublicCategoryOut.build(c, n) for c, n in catalogue.categories()])


@router.get("/categories/{slug}", response_model=DataResponse[PublicCategoryOut])
def category(slug: str, catalogue: Catalogue) -> DataResponse[PublicCategoryOut]:
    return DataResponse(data=PublicCategoryOut.build(*catalogue.category(slug)))


@router.get("/products", response_model=Page[PublicProductOut], summary="Browse / search products")
def products(
    catalogue: Catalogue,
    db: DbSession,
    pagination: PublicPagination,
    search: Annotated[str | None, Query(max_length=MAX_SEARCH_LENGTH)] = None,
    category: Annotated[str | None, Query(max_length=140, description="Category slug")] = None,
    min_price: Annotated[Decimal | None, Query(ge=0)] = None,
    max_price: Annotated[Decimal | None, Query(ge=0)] = None,
    in_stock: bool = False,
    on_offer: bool = False,
    featured: bool = False,
    sort: PublicSort = PublicSort.NAME_ASC,
) -> Page[PublicProductOut]:
    filters = PublicFilters(search, category, min_price, max_price, in_stock, on_offer, featured, sort)
    return paginate(
        db,
        catalogue.products_query(filters),
        pagination,
        lambda p: PublicProductOut.build(p, catalogue.offers_enabled),
    )


def _highlight(
    catalogue: PublicCatalogue, db: DbSession, filters: PublicFilters
) -> DataResponse[list[PublicProductOut]]:
    stmt = catalogue.products_query(filters).limit(PUBLIC_HIGHLIGHT_LIMIT)
    return DataResponse(data=[PublicProductOut.build(p, catalogue.offers_enabled) for p in db.scalars(stmt).unique()])


@router.get("/products/featured", response_model=DataResponse[list[PublicProductOut]], summary="Featured strip")
def featured(catalogue: Catalogue, db: DbSession) -> DataResponse[list[PublicProductOut]]:
    return _highlight(catalogue, db, PublicFilters(featured=True))


@router.get("/products/new", response_model=DataResponse[list[PublicProductOut]], summary="Recently added strip")
def new_arrivals(catalogue: Catalogue, db: DbSession) -> DataResponse[list[PublicProductOut]]:
    return _highlight(catalogue, db, PublicFilters(sort=PublicSort.NEWEST))


@router.get("/products/offers", response_model=DataResponse[list[PublicProductOut]], summary="Special offers strip")
def offers(catalogue: Catalogue, db: DbSession) -> DataResponse[list[PublicProductOut]]:
    """Empty when the admin has switched offers off."""
    return _highlight(catalogue, db, PublicFilters(on_offer=True, sort=PublicSort.PRICE_ASC))


@router.get("/products/{slug}", response_model=DataResponse[PublicProductOut], summary="Product details")
def product(slug: str, catalogue: Catalogue) -> DataResponse[PublicProductOut]:
    return DataResponse(data=PublicProductOut.build(catalogue.product(slug), catalogue.offers_enabled))
