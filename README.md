# Smart Kirana

Kirana store management app with Admin, Seller and Customer panels.

| Part | Tech |
|---|---|
| Backend API (`backend/`) | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, MySQL 8 |
| App (`mobile/`) | React Native (Expo SDK 58, TypeScript, Expo Router): Android, iOS and web |

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
npm start              # Expo Go on a phone, or press w for the web
npm run check          # lint + typecheck + tests
```
