#!/usr/bin/env bash
# Start/stop the Karmine backend (FastAPI + Postgres) and frontend (Vite) dev servers.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT_DIR/.dev-pids"
LOG_DIR="$ROOT_DIR/.dev-logs"
BACKEND_PORT=8001
FRONTEND_PORT=5173

# npm/node are installed via Homebrew but not linked onto PATH by default.
export PATH="/usr/local/opt/node/bin:$PATH"

mkdir -p "$PID_DIR" "$LOG_DIR"

port_pid() {
  lsof -ti":$1" -sTCP:LISTEN 2>/dev/null || true
}

start_postgres() {
  if pg_isready >/dev/null 2>&1; then
    echo "postgres: already running"
    return
  fi
  echo "postgres: starting via brew services..."
  brew services start postgresql@15
  for _ in $(seq 1 10); do
    pg_isready >/dev/null 2>&1 && break
    sleep 1
  done
}

start_backend() {
  local pid
  pid=$(port_pid "$BACKEND_PORT")
  if [ -n "$pid" ]; then
    echo "backend: already running (pid $pid)"
    return
  fi
  echo "backend: starting on :$BACKEND_PORT..."
  cd "$ROOT_DIR"
  nohup poetry run uvicorn app.main:app --port "$BACKEND_PORT" \
    > "$LOG_DIR/backend.log" 2>&1 &
  echo $! > "$PID_DIR/backend.pid"
}

start_frontend() {
  local pid
  pid=$(port_pid "$FRONTEND_PORT")
  if [ -n "$pid" ]; then
    echo "frontend: already running (pid $pid)"
    return
  fi
  echo "frontend: starting on :$FRONTEND_PORT..."
  cd "$ROOT_DIR/frontend"
  nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
  echo $! > "$PID_DIR/frontend.pid"
}

stop_by_port() {
  local name="$1" port="$2" pid
  pid=$(port_pid "$port")
  if [ -z "$pid" ]; then
    echo "$name: not running"
    return
  fi
  echo "$name: stopping (pid $pid)"
  kill "$pid" 2>/dev/null || true
}

status() {
  for entry in "backend:$BACKEND_PORT" "frontend:$FRONTEND_PORT"; do
    name="${entry%%:*}"; port="${entry##*:}"
    pid=$(port_pid "$port")
    if [ -n "$pid" ]; then
      echo "$name: running on :$port (pid $pid)"
    else
      echo "$name: not running"
    fi
  done
  if pg_isready >/dev/null 2>&1; then
    echo "postgres: running"
  else
    echo "postgres: not running"
  fi
}

case "${1:-start}" in
  start)
    start_postgres
    start_backend
    start_frontend
    echo
    echo "backend:  http://127.0.0.1:$BACKEND_PORT"
    echo "frontend: http://localhost:$FRONTEND_PORT"
    echo "logs:     $LOG_DIR/"
    ;;
  stop)
    stop_by_port "backend" "$BACKEND_PORT"
    stop_by_port "frontend" "$FRONTEND_PORT"
    ;;
  status)
    status
    ;;
  *)
    echo "usage: $0 {start|stop|status}"
    exit 1
    ;;
esac
