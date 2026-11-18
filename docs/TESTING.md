# Smart Kirana – Testing

Status at the end of Phase 11 (19-11-2026).

| | Result |
|---|---|
| Backend tests | **223 passed**, code coverage **97%** |
| App tests | **98 passed** (logic, screens in light/dark × English/Punjabi, contrast, translations) |
| Lint / type checks | Clean (ruff, ESLint, TypeScript) |
| Backend dependency audit (`pip-audit`) | No known vulnerabilities |
| App dependency audit (`npm audit --omit=dev`) | 20 moderate, all in development tools (Jest, Expo build tooling) — none ship in the app |
| Web build (`expo export --platform web`) | Builds |
| Real Android / iOS devices | **Not yet tested** — see the device checklist below |

## How to run the checks

```bash
# Backend (needs MySQL and the kirana_test database)
cd backend
uv run pytest                      # all tests
uv run pytest --cov=app            # with coverage
uv run ruff check . && uv run ruff format --check .
uvx pip-audit -r <(uv export --no-dev --no-hashes --format requirements-txt)

# App (Node.js 22.13+)
cd mobile
npm run check                      # lint + typecheck + tests
npx jest --coverage
npx expo export --platform web     # proves every screen compiles
```

Backend tests run against a real MySQL test database (not SQLite), so CHECK constraints, generated columns and row
locks behave exactly as in production. Each test runs in a transaction that is rolled back.

## What the tests cover

### Backend

| Area | Highlights |
|---|---|
| Login & sessions | Tokens, refresh rotation, logout one/all devices, expired vs. invalid tokens, inactive accounts, rate limits (per email+IP and per IP) |
| Password reset | Emailed code, hashed storage, 15-minute expiry, 5-attempt lock, no account enumeration, email in the user's language |
| Permissions | **Permission matrix**: for every protected action, the permission grants access and its absence gives 403; "Add products" is admin-only; sellers never reach admin routes; other stores' data looks like "not found" |
| Customer privacy | Every public endpoint is scanned recursively — no cost, profit, notes, SKU, barcode or stock quantity can appear |
| Catalogue | Price rules (selling ≤ MRP, offer < selling), whole numbers for pcs, slugs, SKUs, image re-encoding, 6-image limit |
| Stock | FEFO across batches, expired batches never sold, ledger maths and immutability, idempotent retries, **real two-thread concurrency test** (no overselling) |
| Expiry | Buckets, cumulative windows, admin-editable limits, India-time midnight boundary |
| Reports | Permission filtering of reports and columns, totals, CSV (Punjabi headings) and Excel (number formats), formula-injection safety |
| Notifications | One alert per problem, recovery, recipients by permission, store switches, personal preferences, language, daily digest once a day, dead device tokens removed |
| End to end | A full **shop day**: setup → stock in → FEFO sale → loose kg sale → low-stock alert → customer view → seller limits → write-off → valuation |

### App

| Area | Highlights |
|---|---|
| Formatting | ₹ with Indian grouping (₹1,23,456.50), DD-MM-YYYY in India time, quantities |
| API client | Language header, field errors, network errors, **single shared token refresh**, logout on deactivation, permission reload on refusal |
| Permissions | Which tabs, fields and buttons each seller sees; permission-editor dependencies and presets |
| Screens | Customer home, product page, login and staff dashboard render in **light/dark × English/Punjabi** |
| Accessibility | Every text colour on every surface meets **WCAG AA 4.5:1** in both themes (checked from the real colour tokens) |
| Translations | English and Punjabi have identical keys, no empty strings, matching `{{placeholders}}`, nothing left untranslated by mistake |

## Security review (Phase 11)

Found and fixed:

1. **Spreadsheet formula injection** — a product named `=HYPERLINK(…)` would have run as a formula when an export was
   opened in Excel. Text cells starting with `= + - @` are now written as plain text.
2. **Login guessing across many emails** — added a per-IP login limit (20/min) on top of the per-email limit.
3. **Browser security headers** — `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`,
   and HSTS in production.
4. **Unsafe production settings** — the API refuses to start in production with DEBUG on, a JWT secret shorter than
   32 characters, or email not configured.
5. **Light-theme readability** — success, warning, danger and accent colours were darkened to pass WCAG AA.

Already in place (verified): Argon2id passwords, hashed refresh tokens and reset codes, timing-safe login, per-device
sessions that end immediately on logout / deactivation, server-side permission checks on every request, store
scoping, `extra="forbid"` request bodies (no mass assignment), ORM queries with escaped LIKE searches, image
re-encoding (EXIF/GPS and hidden payloads removed, decompression-bomb guard), errors without internal details,
API docs disabled in production.

Remaining notes for deployment (Phase 12):

- Run the API behind HTTPS and start it with proxy headers enabled so activity logs record real client IPs.
- The rate limiter keeps counts in memory — fine for one server process; use Redis if running several.
- On the **web**, the login is stored in the browser's local storage (secure storage isn't available on the web).
  The phone apps keep it in the Keychain / Keystore.

## Device checklist (to do on real phones and a browser)

Install the test build on at least one Android phone and one iPhone, and open the website on a laptop and a phone
browser. Tick each item in **both light and dark mode** and **both English and Punjabi**.

**Customer (no login)**
- [ ] Home shows store name, offers, featured, new arrivals, contact buttons; Call and WhatsApp open correctly
- [ ] Categories grid; category page loads more products while scrolling
- [ ] Search finds by name, brand and category; filters and sort work; result count is right
- [ ] Product page: photos swipe, price/MRP/discount, "Only a few left" / "Out of stock", best-before date
- [ ] Punjabi text is not cut off anywhere (buttons, tabs, cards)

**Admin**
- [ ] Log in, log out, forgot password (code arrives by email), change language/theme
- [ ] Add a product with a photo taken on the phone; edit prices; hide/show for customers
- [ ] Stock in (with expiry), stock out (FEFO), adjust count, damaged; history shows each change
- [ ] Expiry tab: tiles, write off an expired batch, edit batch dates
- [ ] Add a seller with a preset; change permissions; deactivate (the seller is logged out on their phone)
- [ ] Reports: open each report, download Excel and CSV, open them in Excel / Google Sheets (Punjabi readable)
- [ ] Store settings: change the store name and logo — the customer home updates
- [ ] Push notification arrives for low stock and for the daily expiry check; tapping it opens the right screen

**Seller**
- [ ] Only permitted tabs and buttons appear; "What you can do" lists the permissions
- [ ] A seller without "View purchase price" never sees costs, profit or stock value at cost
- [ ] When the admin changes permissions, the app updates after returning to it (no new login needed)

**Layouts**
- [ ] Small phone (≈360 px wide), large phone, tablet, desktop browser — no text overlapping, no horizontal scrolling except report tables
- [ ] Largest system font size: text still readable, buttons still tappable
- [ ] Screen reader (TalkBack / VoiceOver) reads buttons and badges sensibly

## Known limitations

- Dates are typed as DD-MM-YYYY (no calendar picker yet).
- Push notifications need the store builds and EAS project from Phase 12; in-app notifications work everywhere now.
- App code coverage is about 62%: logic and key screens are tested; the larger staff screens are covered by type
  checks, the web build and the manual checklist above.
- Punjabi translations were written by the developer and should be reviewed by a native speaker.
