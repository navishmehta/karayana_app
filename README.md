# Smart Kirana

Cloud-based kirana store management: Laravel REST API (`backend/`) + Flutter app (`mobile/`, coming in Phase 6).

## Backend – local setup

Requirements: PHP 8.3+, Composer, MySQL 8.0.16+.

```bash
cd backend
composer install
cp .env.example .env          # set DB_* and ADMIN_EMAIL / ADMIN_PASSWORD
php artisan key:generate
php artisan migrate --seed    # creates store, roles, permissions, admin, units, starter categories
php artisan serve             # http://localhost:8000/api/v1/health
```

Tests run against a separate MySQL database (`smart_kirana_test`, see `backend/phpunit.xml`):

```bash
php artisan test
```

Optional: the stock ledger also gets DB-level append-only triggers if the MySQL user may create
triggers (`log_bin_trust_function_creators=1` or SUPER). Without that, the model-level guard still applies.
