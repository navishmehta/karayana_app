"""Pagination helper for list endpoints."""

import math
from collections.abc import Callable, Sequence
from typing import Annotated, Any, TypeVar

from fastapi import Depends, Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_PER_PAGE, MAX_PER_PAGE
from app.schemas.common import Page, PageMeta, PageParams

T = TypeVar("T")


def page_params(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=MAX_PER_PAGE)] = DEFAULT_PER_PAGE,
) -> PageParams:
    return PageParams(page=page, per_page=per_page)


Pagination = Annotated[PageParams, Depends(page_params)]


def paginate[T](db: Session, stmt: Select, params: PageParams, to_item: Callable[[Any], T]) -> Page[T]:
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows: Sequence[Any] = db.scalars(stmt.limit(params.per_page).offset((params.page - 1) * params.per_page)).all()
    return Page[T](
        data=[to_item(row) for row in rows],
        meta=PageMeta(
            page=params.page,
            per_page=params.per_page,
            total=total,
            last_page=max(1, math.ceil(total / params.per_page)),
        ),
    )


def paginate_rows[T](db: Session, stmt: Select, params: PageParams, to_item: Callable[[Any], T]) -> Page[T]:
    """Like paginate(), for queries that select several columns (e.g. a model plus a count)."""
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.execute(stmt.limit(params.per_page).offset((params.page - 1) * params.per_page)).all()
    return Page[T](
        data=[to_item(row) for row in rows],
        meta=PageMeta(
            page=params.page,
            per_page=params.per_page,
            total=total,
            last_page=max(1, math.ceil(total / params.per_page)),
        ),
    )
