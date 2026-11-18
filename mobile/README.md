# Smart Kirana – app

React Native (Expo SDK 58, TypeScript, Expo Router). One codebase for Android, iOS and the web (customer catalogue).

## Run locally

Requirements: **Node.js 22.13+** (see `.nvmrc`), and the backend API running (see `../backend`).

```bash
cd mobile
npm install
cp .env.example .env   # EXPO_PUBLIC_API_URL: on a phone use your computer's LAN IP, e.g. http://192.168.1.20:8000
npm start              # scan the QR code with Expo Go, or press w for the web
npm run check          # lint + typecheck + tests
```

For the web app, add its address to the backend's `CORS_ORIGINS` (default dev address: `http://localhost:8081`).

## Where things live

| Folder | Contents |
|---|---|
| `src/app/` | Screens (Expo Router: every file is a route) |
| `src/components/ui/` | Shared building blocks: AppText, Button, TextField, Card, Screen, Badge, dialogs, loading/empty/error states |
| `src/constants/` | `config.ts` (API address), `app.ts` (fixed app values), `permissions.ts` |
| `src/theme/` | Design tokens (colours for light/dark, spacing, fonts) and the theme provider |
| `src/i18n/` | Translations: `locales/en.json`, `locales/pa.json` |
| `src/api/` | HTTP client (auth, language, refresh), endpoint functions, types, error codes |
| `src/auth/` | Login session store and permission helpers |
| `src/lib/` | Device storage, React Query client, form validation |
| `src/utils/` | Formatting (₹, DD-MM-YYYY, quantities) and error helpers |
