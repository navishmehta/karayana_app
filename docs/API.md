# Smart Kirana – API

Base URL: `https://<DOMAIN>/api/v1` (locally `http://127.0.0.1:8000/api/v1`).

- **Full reference:** [`docs/api/openapi.json`](api/openapi.json). Import it into Postman/Insomnia, or open it at
  [editor.swagger.io](https://editor.swagger.io). When running locally, interactive docs are at `/docs`.
  Regenerate after changing endpoints: `cd backend && uv run python -m app.cli export-openapi`
  (a test fails if the file is out of date).
- In production `/docs` and `/openapi.json` are switched off.

## Conventions

| Topic | Rule |
|---|---|
| Format | JSON, UTF-8. Request bodies reject unknown fields. |
| Single item | `{"data": {...}}` |
| Lists | `{"data": [...], "meta": {"page", "per_page", "total", "last_page"}}` · `?page=1&per_page=20` (max 100; public max 50) |
| Money | Strings with 2 decimals: `"285.00"` (never floats) · currency INR |
| Quantities | Strings with up to 3 decimals: `"1.250"` (kg/L), whole numbers for pcs |
| Dates | `YYYY-MM-DD` in requests and responses (the app shows DD-MM-YYYY); times are ISO 8601 in India time (`+05:30`) |
| Language | Send `Accept-Language: pa` or `en`. Messages and errors come back in that language. |
| Retries | Stock changes accept an `Idempotency-Key` header; sending the same request twice changes stock once. |

## Login

```http
POST /auth/login        {"email": "...", "password": "...", "device_name": "Shop phone"}
→ {"data": {"access_token", "refresh_token", "access_token_expires_at", "refresh_token_expires_at",
            "user": {..., "role": "seller", "permissions": ["stock.view", ...]}}}
```

- Send `Authorization: Bearer <access_token>` on every staff request. Access tokens last **15 minutes**.
- On `401` with code `TOKEN_EXPIRED`, call `POST /auth/refresh {"refresh_token"}` once. Each refresh token works
  **once** (it is replaced) and lasts 30 days. If refresh fails, log in again.
- `POST /auth/logout` ends this device; `POST /auth/logout-all` ends every device. Deactivating a seller ends all
  their sessions immediately.

## Errors

```json
{ "message": "Not enough stock.", "code": "STOCK_INSUFFICIENT", "errors": { "quantity": ["Only 4 available."] } }
```

| HTTP | `code` | Meaning |
|---|---|---|
| 401 | `UNAUTHENTICATED`, `TOKEN_EXPIRED`, `INVALID_CREDENTIALS` | Not logged in / log in again |
| 403 | `FORBIDDEN`, `ACCOUNT_INACTIVE` | Missing the permission / account deactivated |
| 404 | `NOT_FOUND` | Missing — also returned for another store's data |
| 409 | `CONFLICT`, `CATEGORY_NOT_EMPTY`, `IN_USE`, `STOCK_INSUFFICIENT`, `BATCH_EXPIRED`, `BATCH_NOT_EXPIRED` | Business rule stopped it |
| 413 / 422 | `IMAGE_TOO_LARGE`, `INVALID_IMAGE`, `IMAGE_LIMIT_REACHED`, `VALIDATION_FAILED`, `INVALID_RESET_CODE` | Fix the input (see `errors`) |
| 429 | `TOO_MANY_REQUESTS` | Rate limit (login 5/min per email, 20/min per IP; reset 3/min; public 120/min) |
| 500 | `SERVER_ERROR` | No internal details are ever returned |

## Endpoint groups

| Group | Paths | Who |
|---|---|---|
| Health | `GET /health` | Anyone (checks the database) |
| Public catalogue | `/public/store`, `/public/categories`, `/public/products` (+ `featured`, `new`, `offers`, `{slug}`) | Anyone, no login. Never contains cost, profit, SKU, barcode, notes or stock counts — only `in_stock` / `low_stock` / `out_of_stock` |
| Auth & profile | `/auth/*`, `/devices` (push tokens) | Staff |
| Dashboard | `/dashboard` | `dashboard.view` |
| Catalogue | `/categories`, `/products`, `/units`, `/brands`, `/products/{id}/images` | `products.*`, `categories.*` (creating products: admin only) |
| Stock | `/inventory/stock-in`, `stock-out`, `adjust`, `damage`, `expired-writeoff`, `/inventory/transactions`, `/products/{id}/batches`, `/batches/{id}` | `stock.view`, `stock.update`, `expiry.update` |
| Expiry | `/expiry/summary`, `/expiry/batches` | `expiry.view` |
| Reports | `/reports`, `/reports/{kind}`, `/reports/{kind}/export?format=csv\|xlsx` | `reports.view`, `reports.export` (cost columns need `pricing.view_purchase`) |
| Notifications | `/notifications`, `/notifications/preferences` | Staff |
| Admin | `/admin/sellers`, `/admin/permissions`, `/admin/activity-logs`, `/admin/settings`, `/admin/units`, `/admin/brands`, `/admin/products/{id}/restore` | Admin only |

## Permissions

Defined in `backend/app/enums/permission.py` (one place). The admin has all of them; sellers get the ones ticked in
**Sellers → Permissions**.

| Area | Permissions |
|---|---|
| Dashboard | `dashboard.view` |
| Products | `products.view`, `products.create` (admin only), `products.update`, `products.delete` |
| Categories | `categories.view`, `categories.create`, `categories.update`, `categories.delete` |
| Prices | `pricing.view_purchase`, `pricing.view_selling`, `pricing.update_selling` |
| Stock | `stock.view`, `stock.update` |
| Expiry | `expiry.view`, `expiry.update` |
| Reports | `reports.view`, `reports.export` |

Some permissions need others (e.g. `stock.update` needs `stock.view`). The server rejects a set with a missing
dependency (`422`); the app's permission editor ticks the required ones automatically.

## Example

```bash
API=https://shop.example.com/api/v1
TOKEN=$(curl -s -X POST $API/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"owner@example.com","password":"…","device_name":"curl"}' | jq -r .data.access_token)

curl -s -X POST $API/inventory/stock-in -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{"product_id":12,"quantity":"24","purchase_price":"42.50","expiry_date":"2027-03-31"}'
```
