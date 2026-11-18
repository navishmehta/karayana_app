# Smart Kirana – Deployment

How to put the website and API on a server, build the phone apps, and keep everything running.

```
Phone apps ─┐
Website ────┼── https://shop.example.com ── Caddy (HTTPS, website files, /media)
            │                                  └── /api ── FastAPI ── MySQL 8.4
            │                                                 └── cron: expiry alerts, nightly stock refresh, backups
Push alerts ← Expo push service ← API
```

Everything runs on **one small Linux server** with Docker Compose (`deploy/`). The website and API share one domain,
so there is no CORS to configure and one HTTPS certificate covers both.

| File in `deploy/` | Purpose |
|---|---|
| `docker-compose.yml` | The three services: `db` (MySQL), `api` (FastAPI), `web` (Caddy + website) |
| `Caddyfile` | HTTPS, website (with deep-link fallback), `/api` proxy, `/media` images, caching |
| `web.Dockerfile` | Builds the website from `mobile/` with the production API address baked in |
| `.env.example` | Every production setting — copy to `.env` on the server |
| `server-setup.sh` | One-time server preparation (Docker, firewall, automatic security updates) |
| `deploy.sh` | Install or update: pull, build, backup, migrate, start, seed |
| `backup.sh` / `restore.sh` | Database (daily) and photos (weekly) backups, optional off-site copy |
| `crontab` | Scheduled jobs |

---

## 1. Server

Any VPS with **Ubuntu 24.04, 1 vCPU, 2 GB RAM, 25 GB disk** is enough for one store. Choose a data centre in India
for speed, e.g. DigitalOcean (Bangalore), AWS Lightsail (Mumbai) or Hetzner/Vultr/Linode (Mumbai).

1. Create the server with your SSH key.
2. In your domain's DNS, add an **A record**: `shop.example.com → <server IP>` (and `AAAA` for IPv6 if available).
3. On the server:

```bash
sudo mkdir -p /opt/smart-kirana && sudo chown "$USER" /opt/smart-kirana
git clone https://github.com/<you>/<repo>.git /opt/smart-kirana
cd /opt/smart-kirana/deploy
sudo ./server-setup.sh          # Docker, firewall (SSH, 80, 443 only), automatic security updates
# log out and back in so your user can run docker
```

## 2. Settings

```bash
cp .env.example .env
nano .env
```

| Setting | What to put |
|---|---|
| `DOMAIN` | The domain from step 1 |
| `DB_PASSWORD`, `DB_ROOT_PASSWORD` | `openssl rand -hex 24` (each different) |
| `JWT_SECRET` | `openssl rand -hex 32` — the API refuses to start with less than 32 characters |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | The owner's first login (change the password in the app afterwards) |
| `SMTP_*`, `MAIL_FROM_*` | Email for password-reset codes. Brevo's free plan (300 emails/day) is plenty; Amazon SES or a Gmail app password also work |
| `EXPO_PUSH_ACCESS_TOKEN` | Optional; only if "enhanced push security" is turned on in your Expo account |
| `RCLONE_REMOTE` | Optional off-site backup target (see section 5) |

`.env` holds secrets — it is git-ignored. Keep a copy in a password manager.

## 3. First deploy

```bash
./deploy.sh
crontab crontab                   # scheduled jobs (see the file for times)
```

Check:

- `https://<DOMAIN>` — the customer website
- `https://<DOMAIN>/api/v1/health` — `{"status":"ok", ...}`
- Log in as the admin, open **Store settings**, fill in phone, WhatsApp, address and hours, upload a logo.

The API refuses to start in production if `DEBUG` is on, `JWT_SECRET` is too short, or email is not set to SMTP —
check `docker compose logs api` if the health check fails.

## 4. Updates

```bash
cd /opt/smart-kirana/deploy && ./deploy.sh
```

`deploy.sh` backs up the database **before** running migrations, so a failed update can be rolled back with
`restore.sh`. GitHub Actions (`.github/workflows/ci.yml`) runs every test and builds both images on each push;
deploy only when it is green.

## 5. Backups

| What | When | Kept |
|---|---|---|
| Database (`mysqldump`, gzipped) | Daily 02:30 IST | 30 days in `deploy/backups/` |
| Product photos and logo | Sundays | 30 days |
| Off-site copy (optional) | After each backup | As your storage provider keeps it |

A backup on the same server does not survive the server being lost. Set up an off-site copy:

```bash
sudo apt install rclone && rclone config       # e.g. a Cloudflare R2 or Backblaze B2 bucket named "r2"
# then in .env:  RCLONE_REMOTE=r2:kirana-backups
```

**Test a restore every few months** (on a spare server or locally):

```bash
./restore.sh backups/db_2026-11-20_2100.sql.gz   # asks you to type RESTORE (file times are UTC)
```

## 6. Monitoring

- Add a free **UptimeRobot** (or Better Stack) monitor on `https://<DOMAIN>/api/v1/health` — it checks the database
  too, and emails you if the site goes down.
- Logs: `docker compose logs -f api`, `docker compose logs -f web`, scheduled jobs in `deploy/cron.log`.
- Disk space: `df -h` (backups and photos grow slowly; 25 GB lasts years for one store).

---

## 7. Phone apps (Expo EAS)

The apps are built in the cloud by **Expo Application Services (EAS)**; no Mac is needed, even for the iPhone app.

### One-time setup

```bash
cd mobile
npm install -g eas-cli
eas login                       # create a free account at expo.dev first
eas init                        # creates the project and prints its ID
```

Put the project ID and your domain into `mobile/eas.json` (`build.base.env`):

```json
"EXPO_PUBLIC_API_URL": "https://shop.example.com",
"EAS_PROJECT_ID": "<id from eas init>"
```

(`app.config.ts` reads these; push notifications need the project ID.)

### Push notification credentials

| Platform | Steps |
|---|---|
| Android | 1. In the [Firebase console](https://console.firebase.google.com) create a project and add an Android app with package `com.smartkirana.app`. 2. Download `google-services.json` into `mobile/` (it is git-ignored; for cloud builds upload it with `eas env:create --name GOOGLE_SERVICES_FILE --type file`). 3. Firebase → Project settings → Service accounts → generate a private key. 4. `eas credentials` → Android → Push notifications (FCM V1) → upload that key. |
| iPhone | Needs the Apple Developer Program. `eas credentials` → iOS → creates the push key for you. |

### Builds

| Command | Gives you | Use it for |
|---|---|---|
| `eas build -p android --profile preview` | An **APK** link | Install directly on shop phones for testing — no Play Store needed |
| `eas build -p android --profile production` | An **AAB** | Google Play |
| `eas build -p ios --profile production` | An **IPA** | App Store / TestFlight |
| `eas build --profile development` | A dev build | Developers only (`npx expo start --dev-client`) |

Version numbers are managed by EAS (`appVersionSource: remote`, `autoIncrement` on production builds).
Change the user-visible version in `mobile/app.json` (`expo.version`).

### Store submission

```bash
eas submit -p android --profile production    # uploads to Play Console (internal testing track, as a draft)
eas submit -p ios --profile production        # uploads to App Store Connect / TestFlight
```

**Google Play checklist** (Play Console, one-time US$25):

- [ ] App name, short and full description (English and Punjabi), app icon (512×512: `mobile/assets/images/icon.png`)
- [ ] At least 2 phone screenshots (customer home, product page, staff dashboard)
- [ ] Privacy policy URL: `https://<DOMAIN>/privacy`
- [ ] Data safety form: collects **email, name, phone (staff only)**, **photos (staff uploads)**, **device ID (push token)**;
      no data sold or shared; data encrypted in transit; users can request deletion
- [ ] Content rating questionnaire (no objectionable content), target audience 18+, no ads
- [ ] App access: give the reviewer a **test seller login** (staff screens are behind login)
- [ ] New personal developer accounts must run a closed test with testers for 14 days before going public

**Apple App Store checklist** (Apple Developer Program, US$99/year):

- [ ] App Store Connect: name, subtitle, description, keywords, support URL, privacy policy URL `https://<DOMAIN>/privacy`
- [ ] Screenshots for 6.9" and 6.5" iPhones (and iPad if tablet support stays on)
- [ ] App Privacy answers matching the Play data-safety form
- [ ] Review notes with a test login
- [ ] Export compliance is already answered in `app.json` (`usesNonExemptEncryption: false`)

### App icon

The icon, Android adaptive icon layers, splash mark and favicon are drawn by `mobile/scripts/make_icons.py`
(colours at the top of the file). To change them: edit, then run
`../backend/.venv/bin/python scripts/make_icons.py` from `mobile/`.

---

## Accounts you need

| Service | Needed for | Cost |
|---|---|---|
| VPS provider | Website + API | About ₹500–1,000 / month |
| Domain | `shop.example.com` | About ₹800–1,500 / year |
| SMTP (e.g. Brevo) | Password-reset emails | Free tier |
| Expo | App builds, push | Free tier (30 builds/month) |
| Firebase | Android push | Free |
| Google Play Console | Android app | US$25 once |
| Apple Developer | iPhone app | US$99 / year (optional — skip if all staff use Android) |
| Off-site storage (optional) | Backups | Cloudflare R2: free up to 10 GB |
