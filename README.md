# Smart Kirana

Kirana store management app with Admin, Seller and Customer panels.

| Part | Tech |
|---|---|
| Backend API (`backend/`) | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, MySQL 8 |
| App (`mobile/`) | React Native (Expo SDK 58, TypeScript, Expo Router): Android, iOS and web |

| Guide | Contents |
|---|---|
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Server, HTTPS, backups, monitoring, phone app builds, store submission |
| [docs/API.md](docs/API.md) | API conventions, login, errors, permissions (full reference: `docs/api/openapi.json`) |
| [docs/TESTING.md](docs/TESTING.md) | Test status, how to run every check, security review, device checklist |
| [docs/FUTURE.md](docs/FUTURE.md) | V2–V4 ideas (billing, purchases, customer orders, more shops) and where to start |

Every push to `main` runs the tests in GitHub Actions (`.github/workflows/ci.yml`) and, when they pass, goes live
automatically at **https://kirana.thecodemate.com** (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#live-server-kiranathecodematecom-hostinger-vps)).

## Run everything locally (one command)

```bash
npm start        # from the project folder (or from mobile/)
```

Starts MySQL (if stopped), the backend and the app, set up for phones on the same Wi-Fi: scan the QR code with
Expo Go, or open the printed website address. Backend output (including password-reset codes) goes to
`backend/dev-server.log`. **Ctrl+C** stops everything. The script is `scripts/dev.sh`; first-time setup of each
part is below.

### Demo data for testing

```bash
cd backend && uv run python -m app.cli seed-demo
```

Fills an **empty** local shop with a realistic month: 52 products in all categories (photos, offers, featured,
hidden, loose items by kg), one deleted product, 4 sellers with different permissions (one deactivated) and
30 days of history — deliveries, sales, damage, count corrections and expiry write-offs — so the dashboard
charts, reports, alerts, notifications and activity log all have data. Some products end up low or out of
stock and some batches are expired or about to expire. It refuses to run in production or on a shop that
already has products. Seller logins: `gurpreet@demo.test`, `aman@demo.test`, `simran@demo.test`
(password `Demo@1234`; `rohit@demo.test` is deactivated). The shop is defined in `backend/app/db/demo_data.py`.

## Offline mode

- Everything a person has opened stays readable without internet (saved on the device for 7 days), and photos
  are cached. Staff can open the app offline: the staff side opens with the saved login.
- **Stock changes work offline**: stock in / out / count / damage are saved on the phone and sent automatically
  when the connection returns, in order. Each keeps its Idempotency-Key, so nothing is ever counted twice.
  If the server refuses one (e.g. not enough stock), it stays under **More → Unsent changes** with the reason.
- Other changes (products, prices, sellers, settings) need internet; the app says so.
- An unexpected error on a screen shows a "Try again" page instead of closing the app.

## Backend – local setup

Requirements: [uv](https://docs.astral.sh/uv/) (installs Python 3.12 itself) and MySQL 8.0.16+.

```bash
cd backend
uv sync                              # install dependencies
cp .env.example .env                 # set DATABASE_URL, ADMIN_EMAIL, ADMIN_PASSWORD
uv run alembic upgrade head          # create tables
uv run python -m app.cli seed        # store, roles, permissions, admin, units, settings, starter categories
uv run fastapi dev app/main.py       # http://127.0.0.1:8000/api/v1/health  ·  API docs at /docs
```

Tests use a separate MySQL database (default `kirana_test`, override with `TEST_DATABASE_URL`):

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

### Scheduled jobs (installed on the server from `deploy/crontab`)

| When (store time, IST) | Command | Why |
|---|---|---|
| Every 15 minutes | `uv run python -m app.cli send-expiry-alerts` | Sends the daily expiry summary once, at the time set in Store settings |
| 00:05 daily | `uv run python -m app.cli refresh-stock` | Batches that expired at midnight stop counting as sellable; may trigger stock alerts |
| 02:30 daily | `deploy/backup.sh` | Database backup (photos on Sundays) — production only |

Push notifications: `PUSH_DRIVER=log` writes them to the log locally; `PUSH_DRIVER=expo` sends through Expo's push service
(Android via Firebase Cloud Messaging, iOS via APNs — credentials are uploaded to EAS, not stored on this server).

### Where to change things

| To change… | Edit… |
|---|---|
| Database, admin login, timezone, allowed web origins | `backend/.env` (read by `app/core/config.py`) |
| Store name, logo, contact details, thresholds | In the app's admin settings (stored in `app_settings`) |
| Permissions, roles, error codes, setting keys | `backend/app/enums/` |
| Fixed technical values (decimal places, page sizes, date formats) | `backend/app/core/constants.py` |
| Message text in English / Punjabi | `backend/app/locales/en.json`, `pa.json` |
| Starter units and categories | `backend/app/db/seed_data.py` |

## App – local setup

Requirements: Node.js 22.13+ and the backend running. Details in [`mobile/README.md`](mobile/README.md).

```bash
cd mobile
npm install
cp .env.example .env   # EXPO_PUBLIC_API_URL
npm run start:app      # the app only (npm start also starts the backend)
npm run check          # lint + typecheck + tests
```
