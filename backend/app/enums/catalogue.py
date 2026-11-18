"""Sort options and media folders for the catalogue."""

from enum import StrEnum

from sqlalchemy import ColumnElement

from app.enums.permission import Permission
from app.models import Category, Product


class ProductSort(StrEnum):
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    NEWEST = "newest"
    STOCK_ASC = "stock_asc"

    @property
    def required_permission(self) -> Permission | None:
        """Sorting by a value the user can't see would leak it, so it needs the same permission."""
        match self:
            case ProductSort.PRICE_ASC | ProductSort.PRICE_DESC:
                return Permission.PRICING_VIEW_SELLING
            case ProductSort.STOCK_ASC:
                return Permission.STOCK_VIEW
            case _:
                return None

    @property
    def order_by(self) -> tuple[ColumnElement, ...]:
        return {
            ProductSort.NAME_ASC: (Product.name.asc(), Product.id.asc()),
            ProductSort.NAME_DESC: (Product.name.desc(), Product.id.desc()),
            ProductSort.PRICE_ASC: (Product.selling_price.asc(), Product.name.asc()),
            ProductSort.PRICE_DESC: (Product.selling_price.desc(), Product.name.asc()),
            ProductSort.NEWEST: (Product.created_at.desc(), Product.id.desc()),
            ProductSort.STOCK_ASC: (Product.sellable_stock.asc(), Product.name.asc()),
        }[self]


class CategorySort(StrEnum):
    POSITION = "position"
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    NEWEST = "newest"

    @property
    def order_by(self) -> tuple[ColumnElement, ...]:
        return {
            CategorySort.POSITION: (Category.sort_order.asc(), Category.name.asc()),
            CategorySort.NAME_ASC: (Category.name.asc(),),
            CategorySort.NAME_DESC: (Category.name.desc(),),
            CategorySort.NEWEST: (Category.created_at.desc(), Category.id.desc()),
        }[self]


class MediaFolder(StrEnum):
    CATEGORIES = "categories"
    PRODUCTS = "products"
    STORE = "store"
