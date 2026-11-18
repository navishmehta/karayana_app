"""Every permission in the system.

The admin always has all of them. Sellers get only what the admin grants them one by one,
and only permissions marked grantable can be granted to a seller.
"""

from enum import StrEnum

from app.core.i18n import t


class Permission(StrEnum):
    DASHBOARD_VIEW = "dashboard.view"

    PRODUCTS_VIEW = "products.view"
    PRODUCTS_CREATE = "products.create"  # admin only (business rule)
    PRODUCTS_UPDATE = "products.update"
    PRODUCTS_DELETE = "products.delete"

    CATEGORIES_VIEW = "categories.view"
    CATEGORIES_CREATE = "categories.create"
    CATEGORIES_UPDATE = "categories.update"
    CATEGORIES_DELETE = "categories.delete"

    PRICING_VIEW_PURCHASE = "pricing.view_purchase"
    PRICING_VIEW_SELLING = "pricing.view_selling"
    PRICING_UPDATE_SELLING = "pricing.update_selling"

    STOCK_VIEW = "stock.view"
    STOCK_UPDATE = "stock.update"

    EXPIRY_VIEW = "expiry.view"
    EXPIRY_UPDATE = "expiry.update"

    REPORTS_VIEW = "reports.view"
    REPORTS_EXPORT = "reports.export"

    @property
    def group(self) -> str:
        return self.value.split(".")[0]

    @property
    def label(self) -> str:
        return t(f"permissions.{self.value}")

    @property
    def is_grantable_to_sellers(self) -> bool:
        return self not in _ADMIN_ONLY

    @property
    def depends_on(self) -> tuple["Permission", ...]:
        """Direct dependencies: e.g. stock.update needs stock.view."""
        return _DEPENDENCIES.get(self, ())

    def all_dependencies(self) -> list["Permission"]:
        """Direct and indirect dependencies (stock.update -> stock.view -> products.view)."""
        result: list[Permission] = []
        for dependency in self.depends_on:
            for item in (dependency, *dependency.all_dependencies()):
                if item not in result:
                    result.append(item)
        return result

    @classmethod
    def grantable(cls) -> list["Permission"]:
        return [p for p in cls if p.is_grantable_to_sellers]

    @classmethod
    def missing_dependencies(cls, granted: set["Permission"]) -> dict["Permission", list["Permission"]]:
        """For each granted permission, the dependencies that are not granted."""
        missing: dict[Permission, list[Permission]] = {}
        for permission in granted:
            absent = [d for d in permission.all_dependencies() if d not in granted]
            if absent:
                missing[permission] = absent
        return missing


_ADMIN_ONLY: frozenset[Permission] = frozenset({Permission.PRODUCTS_CREATE})

_DEPENDENCIES: dict[Permission, tuple[Permission, ...]] = {
    Permission.PRODUCTS_CREATE: (Permission.PRODUCTS_VIEW,),
    Permission.PRODUCTS_UPDATE: (Permission.PRODUCTS_VIEW,),
    Permission.PRODUCTS_DELETE: (Permission.PRODUCTS_VIEW,),
    Permission.CATEGORIES_CREATE: (Permission.CATEGORIES_VIEW,),
    Permission.CATEGORIES_UPDATE: (Permission.CATEGORIES_VIEW,),
    Permission.CATEGORIES_DELETE: (Permission.CATEGORIES_VIEW,),
    Permission.PRICING_VIEW_PURCHASE: (Permission.PRODUCTS_VIEW,),
    Permission.PRICING_VIEW_SELLING: (Permission.PRODUCTS_VIEW,),
    Permission.PRICING_UPDATE_SELLING: (Permission.PRICING_VIEW_SELLING,),
    Permission.STOCK_VIEW: (Permission.PRODUCTS_VIEW,),
    Permission.STOCK_UPDATE: (Permission.STOCK_VIEW,),
    Permission.EXPIRY_VIEW: (Permission.PRODUCTS_VIEW,),
    Permission.EXPIRY_UPDATE: (Permission.EXPIRY_VIEW,),
    Permission.REPORTS_EXPORT: (Permission.REPORTS_VIEW,),
}
