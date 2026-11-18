import csv
import io
from datetime import timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import store_today
from app.enums.permission import Permission as Perm
from app.enums.report import ReportType
from app.models import ActivityLog
from app.services.inventory.stock_cache import refresh_product_stock
from tests.helpers import admin_headers, create_seller, make_category, make_product, seller_headers
from tests.test_inventory import _batch

URL = "/api/v1/reports"


def _shop(db: Session):
    category = make_category(db, "Report Dairy")
    milk = make_product(db, "Milk", category_id=category.id, purchase_price=Decimal("20"), selling_price=Decimal("25"),
                        mrp=Decimal("26"), min_stock_level=Decimal(5))  # fmt: skip
    rice = make_product(db, "Rice", category_id=category.id, purchase_price=Decimal("40"), selling_price=Decimal("50"),
                        mrp=None, min_stock_level=Decimal(2))  # fmt: skip
    _batch(db, milk.id, "3", 4)
    _batch(db, rice.id, "10", 90)
    for p in (milk, rice):
        refresh_product_stock(db, p)
    db.commit()
    return category, milk, rice


def test_admin_sees_every_report(client: TestClient) -> None:
    reports = client.get(URL, headers=admin_headers(client)).json()["data"]
    assert {r["key"] for r in reports} == {t.value for t in ReportType}
    assert all(r["can_export"] for r in reports)


def test_sellers_see_only_reports_their_permissions_allow(client: TestClient, seeded_db: Session) -> None:
    perms = [Perm.REPORTS_VIEW, Perm.PRODUCTS_VIEW, Perm.STOCK_VIEW]
    reports = client.get(URL, headers=seller_headers(client, create_seller(seeded_db, perms))).json()["data"]
    assert {r["key"] for r in reports} == {"products", "stock", "low_stock", "stock_movements"}
    assert not reports[0]["can_export"]
    assert (
        client.get(URL, headers=seller_headers(client, create_seller(seeded_db, [Perm.PRODUCTS_VIEW]))).status_code
        == 403
    )


def test_report_requiring_other_permissions_is_forbidden(client: TestClient, seeded_db: Session) -> None:
    perms = [Perm.REPORTS_VIEW, Perm.PRODUCTS_VIEW, Perm.PRICING_VIEW_SELLING]
    headers = seller_headers(client, create_seller(seeded_db, perms))
    assert client.get(f"{URL}/profit_margin", headers=headers).status_code == 403
    assert client.get(f"{URL}/selling_price", headers=headers).status_code == 200


def test_private_columns_are_removed(client: TestClient, seeded_db: Session) -> None:
    _shop(seeded_db)
    perms = [Perm.REPORTS_VIEW, Perm.PRODUCTS_VIEW, Perm.PRICING_VIEW_SELLING]
    data = client.get(f"{URL}/products", headers=seller_headers(client, create_seller(seeded_db, perms))).json()["data"]
    keys = [c["key"] for c in data["columns"]]
    assert "selling_price" in keys and "purchase_price" not in keys
    assert all("purchase_price" not in row for row in data["rows"])


def test_stock_report_rows_totals_and_paging(client: TestClient, seeded_db: Session) -> None:
    category, _, _ = _shop(seeded_db)
    data = client.get(
        f"{URL}/stock", params={"category_id": category.id, "per_page": 1}, headers=admin_headers(client)
    ).json()
    report = data["data"]
    assert report["label"] == "Stock"
    assert report["meta"] == {"page": 1, "per_page": 1, "total": 2, "last_page": 2}
    assert report["rows"][0]["product"] == "Milk"
    assert report["rows"][0]["stock_status"] == "Low stock"
    assert report["totals"] == {"current_stock": "13", "sellable_stock": "13"}


def test_valuation_and_profit_numbers(client: TestClient, seeded_db: Session) -> None:
    category, _, _ = _shop(seeded_db)
    headers = admin_headers(client)
    valuation = client.get(f"{URL}/valuation", params={"category_id": category.id}, headers=headers).json()["data"]
    # cost 3×20 + 10×40 = 460; selling 3×25 + 10×50 = 575
    assert valuation["totals"] == {"cost_value": "460.00", "selling_value": "575.00", "potential_profit": "115.00"}
    profit = client.get(f"{URL}/profit_margin", params={"category_id": category.id}, headers=headers).json()["data"]
    milk = next(r for r in profit["rows"] if r["product"] == "Milk")
    assert (milk["profit"], milk["markup_percent"], milk["margin_percent"]) == ("5.00", "25.00", "20.00")


def test_csv_export_in_punjabi_with_display_dates(client: TestClient, seeded_db: Session) -> None:
    category, _, _ = _shop(seeded_db)
    response = client.get(
        f"{URL}/expiry/export",
        params={"format": "csv", "category_id": category.id, "within_days": 30},
        headers=admin_headers(client) | {"Accept-Language": "pa"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"].startswith('attachment; filename="expiry-')
    assert response.content.startswith(b"\xef\xbb\xbf")  # BOM: Excel opens Gurmukhi correctly
    rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert rows[0][0] == "ਉਤਪਾਦ"
    assert rows[1][0] == "Milk"
    assert (store_today() + timedelta(days=4)).strftime("%d-%m-%Y") in rows[1]
    assert rows[-1][0] == "ਕੁੱਲ"


def test_xlsx_export_has_real_numbers_and_formats(client: TestClient, seeded_db: Session) -> None:
    category, _, _ = _shop(seeded_db)
    response = client.get(
        f"{URL}/valuation/export", params={"format": "xlsx", "category_id": category.id}, headers=admin_headers(client)
    )
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats")
    sheet = load_workbook(io.BytesIO(response.content)).active
    header = [c.value for c in sheet[1]]
    assert header[:2] == ["Product", "SKU"]
    cost_col = header.index("Value at cost") + 1
    assert sheet.cell(row=2, column=cost_col).value == 60.0
    assert sheet.cell(row=2, column=cost_col).number_format == "#,##0.00"
    assert sheet.cell(row=sheet.max_row, column=1).value == "Total"
    assert sheet.cell(row=1, column=1).font.bold


def test_export_needs_permission_and_is_logged(client: TestClient, seeded_db: Session) -> None:
    viewer = seller_headers(client, create_seller(seeded_db, [Perm.REPORTS_VIEW, Perm.STOCK_VIEW, Perm.PRODUCTS_VIEW]))
    assert client.get(f"{URL}/stock/export", headers=viewer).status_code == 403
    exporter = seller_headers(
        client, create_seller(seeded_db, [Perm.REPORTS_VIEW, Perm.REPORTS_EXPORT, Perm.STOCK_VIEW, Perm.PRODUCTS_VIEW])
    )
    assert client.get(f"{URL}/stock/export", params={"format": "csv"}, headers=exporter).status_code == 200
    logged = seeded_db.scalar(select(func.count(ActivityLog.id)).where(ActivityLog.action == "reports.exported"))
    assert logged == 1


def test_stock_movements_follow_date_range(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db, "Moving")
    headers = admin_headers(client)
    body = {"product_id": product.id, "quantity": "5", "expiry_date": (store_today() + timedelta(days=50)).isoformat()}
    client.post("/api/v1/inventory/stock-in", json=body, headers=headers)
    today = store_today().isoformat()
    rows = client.get(f"{URL}/stock_movements", params={"date_from": today, "date_to": today}, headers=headers).json()
    assert [r["movement"] for r in rows["data"]["rows"]] == ["Opening stock"]
    old = (store_today() - timedelta(days=10)).isoformat()
    empty = client.get(f"{URL}/stock_movements", params={"date_from": old, "date_to": old}, headers=headers).json()
    assert empty["data"]["rows"] == []
