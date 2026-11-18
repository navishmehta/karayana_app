from enum import StrEnum


class ReportType(StrEnum):
    PRODUCTS = "products"
    CATEGORIES = "categories"
    STOCK = "stock"
    LOW_STOCK = "low_stock"
    EXPIRY = "expiry"
    PURCHASE_COST = "purchase_cost"
    SELLING_PRICE = "selling_price"
    VALUATION = "valuation"
    PROFIT_MARGIN = "profit_margin"
    STOCK_MOVEMENTS = "stock_movements"


class ColumnKind(StrEnum):
    TEXT = "text"
    INT = "int"
    MONEY = "money"
    QUANTITY = "quantity"
    PERCENT = "percent"
    DATE = "date"
    DATETIME = "datetime"


class ExportFormat(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"

    @property
    def media_type(self) -> str:
        return {
            ExportFormat.CSV: "text/csv; charset=utf-8",
            ExportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }[self]
