#!/usr/bin/env bash
# Local testing in one command:  npm start   (from the project folder or mobile/)
# Starts the backend and the app, set up so phones on the same Wi-Fi can use them.
# Press Ctrl+C to stop both.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_PORT=8000
APP_PORT=8081
BACKEND_LOG="$ROOT/backend/dev-server.log"
MIN_NODE_MAJOR=22

# --- This Mac's address on the Wi-Fi (changes between networks, so it is detected every time) ---
IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || true)"
IP="${IP:-localhost}"
API_URL="http://$IP:$API_PORT"

# --- Node: the app needs 22+; use Homebrew's newer Node if the default is older ---
node_major() { node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0; }
if [ "$(node_major)" -lt "$MIN_NODE_MAJOR" ] && [ -x /opt/homebrew/opt/node/bin/node ]; then
  export PATH="/opt/homebrew/opt/node/bin:$PATH"
fi
[ "$(node_major)" -ge "$MIN_NODE_MAJOR" ] || { echo "Node.js $MIN_NODE_MAJOR+ is needed (found $(node -v 2>/dev/null))."; exit 1; }

# --- MySQL ---
if ! mysqladmin ping -h 127.0.0.1 --silent >/dev/null 2>&1; then
  echo "==> Starting MySQL"
  brew services start mysql >/dev/null
  until mysqladmin ping -h 127.0.0.1 --silent >/dev/null 2>&1; do sleep 1; done
fi

# --- Backend (in the background; its output goes to backend/dev-server.log) ---
BACKEND_PID=""
# uv -> fastapi reloader -> server worker: stop the whole chain, not just the first process.
kill_tree() {
  local child
  for child in $(pgrep -P "$1"); do kill_tree "$child"; done
  kill "$1" 2>/dev/null || true
}
stop_backend() { if [ -n "$BACKEND_PID" ]; then kill_tree "$BACKEND_PID"; BACKEND_PID=""; fi; }
trap stop_backend EXIT
trap 'exit 130' INT TERM

if lsof -iTCP:"$API_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "==> Backend already running on port $API_PORT"
else
  echo "==> Starting the backend (log: backend/dev-server.log)"
  (
    cd "$ROOT/backend"
    # Lets the website opened from a phone (http://<IP>:8081) call the API. Overrides backend/.env for this run only.
    CORS_ORIGINS="[\"http://localhost:$APP_PORT\",\"http://$IP:$APP_PORT\"]" \
      exec uv run fastapi dev app/main.py --host 0.0.0.0 --port "$API_PORT"
  ) >"$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!
  for _ in $(seq 60); do
    curl -sf "http://127.0.0.1:$API_PORT/api/v1/health" >/dev/null && break
    kill -0 "$BACKEND_PID" 2>/dev/null || { echo "Backend failed to start:"; tail -20 "$BACKEND_LOG"; exit 1; }
    sleep 1
  done
fi

cat <<EOF

  Smart Kirana is running
  ─────────────────────────────────────────────
  Phone app (Expo Go):   scan the QR code below
  Website on a phone:    http://$IP:$APP_PORT
  Website on this Mac:   http://localhost:$APP_PORT
  API health:            $API_URL/api/v1/health
  Backend log:           backend/dev-server.log  (password-reset codes appear here)
  Stop everything:       Ctrl+C

EOF

# --- App (in front, so its QR code and keys — r reload, w web — work). Overrides mobile/.env for this run. ---
cd "$ROOT/mobile"
EXPO_PUBLIC_API_URL="$API_URL" npx expo start --lan
