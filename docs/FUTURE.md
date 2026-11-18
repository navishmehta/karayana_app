# Smart Kirana – Future versions

Version 1 was built so the next steps add code instead of rewriting it. For each idea: what already exists and where
to start.

## V2 – Billing and purchases

| Feature | Already in place | Start here |
|---|---|---|
| **Billing / POS** (sell at the counter, print or WhatsApp a bill) | `InventoryService.take_stock()` takes stock by FEFO with row locks and returns the batches used. Each sale can therefore record its exact cost and profit. | New `sales` + `sale_items` tables; a sale calls `take_stock` once per line inside one transaction. Add a `SALE` stock movement type. Barcode lookup already exists: `GET /products/lookup?barcode=`. |
| **Purchases & suppliers** (orders, supplier bills, what's owed) | `product_batches.purchase_item_id` is reserved for linking a batch to the purchase line it came from. `purchase_price` is already stored per batch. | `suppliers`, `purchases`, `purchase_items` tables; receiving a purchase calls `stock_in` per line and sets `purchase_item_id`. |
| **Reports on sales** | `ReportDefinition` (`backend/app/services/reports/definitions.py`): one class per report, with per-column permissions, CSV/Excel export for free. | Add "Sales by day", "Profit by product", "GST summary" definitions. |
| **GST** | Prices are exact decimals. | Add `hsn_code` and `gst_rate` to products; work out tax on sale lines. |
| **Barcode scanning** | Products have `barcode`; lookup endpoint exists. | `expo-camera` barcode scanner on the stock and billing screens. |
| **Date picker** | Dates are typed as DD-MM-YYYY. | Swap the date field for a native picker (`@react-native-community/datetimepicker`). |

## V3 – Customers

| Feature | Already in place | Start here |
|---|---|---|
| **Customer accounts & orders** (order online, pick up / delivery) | A `customer` role is reserved in `backend/app/enums/role.py`. The public catalogue is complete and safe to show. | Enable the role, add phone-OTP login, `orders` / `order_items`; an accepted order becomes a sale (V2). |
| **Credit book (udhaar)** | — | `customer_ledger` table (append-only, like the stock ledger), reminders by WhatsApp. |
| **Offers & loyalty** | `offer_price` and the Offers strip exist. | Time-limited offers (`offer_starts_at`, `offer_ends_at`), points per purchase. |

## V4 – More shops

| Feature | Already in place | Start here |
|---|---|---|
| **Several stores** | Every table has `store_id`, every query is scoped by the user's store, and other stores' data returns "not found". Settings are per store. | Admin screen to add stores; let an owner switch stores; public catalogue by store slug or domain. |
| **Stock transfers between stores** | The stock ledger records every movement with a type and reason. | A transfer = `take_stock` in one store + `stock_in` in the other, in one transaction. |
| **More servers** | The API is stateless except the rate limiter. | Move rate-limit counters to Redis; images to S3/R2 (`MEDIA_DRIVER`; storage is behind one interface in `app/services/storage.py`). |

## Smaller additions

| To add… | Change… |
|---|---|
| **Hindi** (or any language) | `backend/app/locales/hi.json` + `supported_locales` in `backend/app/core/config.py`; `mobile/src/i18n/locales/hi.json`, registered in `mobile/src/i18n/index.ts`, + one line in `LANGUAGES` (`mobile/src/constants/app.ts`). The tests check that every key is translated. |
| A new seller permission | `backend/app/enums/permission.py` (with its dependencies), then the same key in `mobile/src/constants/permissions.ts` and its labels in both locale files. |
| A new setting the owner can change | `backend/app/enums/setting_key.py` (default, and whether customers may see it), its field in `backend/app/schemas/settings.py`, and an input on the app's Store settings screen. |
| A new notification type | `backend/app/enums/notification.py` + a rule in `app/services/notifications/alerts.py`; the app's tap target in `mobile/src/utils/notificationRoutes.ts`. |
