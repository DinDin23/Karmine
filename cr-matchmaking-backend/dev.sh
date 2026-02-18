#!/usr/bin/env bash
# dev.sh — Start / stop all Karmine backend services
# Usage:
#   ./dev.sh          Start Redis, PostgreSQL, and Uvicorn (Ctrl+C to stop)
#   ./dev.sh stopall  Stop Uvicorn, Redis, and PostgreSQL

set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$BACKEND_DIR/.uvicorn.pid"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()   { echo -e "${CYAN}[dev]${NC} $*"; }
ok()    { echo -e "${GREEN}[dev]${NC} $*"; }
warn()  { echo -e "${YELLOW}[dev]${NC} $*"; }
error() { echo -e "${RED}[dev]${NC} $*" >&2; }

# ── Helpers ───────────────────────────────────────────────────────────────────

brew_service_running() {
    brew services list 2>/dev/null | grep -qE "^$1\s+started"
}

start_brew_service() {
    local svc=$1
    if brew_service_running "$svc"; then
        ok "$svc already running — skipping"
        echo "skip"
    else
        log "Starting $svc via brew services..."
        brew services start "$svc" >/dev/null 2>&1 && ok "$svc started" || {
            error "Failed to start $svc — is it installed? (brew install $svc)"
            exit 1
        }
        echo "started"
    fi
}

stop_brew_service() {
    local svc=$1
    log "Stopping $svc..."
    brew services stop "$svc" >/dev/null 2>&1 && ok "$svc stopped" || warn "Could not stop $svc"
}

stop_uvicorn() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log "Stopping Uvicorn (PID $pid)..."
            kill "$pid" 2>/dev/null || true
            wait "$pid" 2>/dev/null || true
            ok "Uvicorn stopped"
        else
            warn "Uvicorn PID $pid not found (already stopped?)"
        fi
        rm -f "$PID_FILE"
    else
        warn "No Uvicorn PID file found — is it running?"
    fi
}

# ── Commands ──────────────────────────────────────────────────────────────────

cmd_start() {
    log "Checking infrastructure services..."

    local redis_status pg_status
    redis_status=$(start_brew_service "redis")
    pg_status=$(start_brew_service "postgresql@15" 2>/dev/null) || \
    pg_status=$(start_brew_service "postgresql")

    if [[ "$redis_status" == "started" || "$pg_status" == "started" ]]; then
        log "Waiting for infrastructure to be ready..."
        sleep 2
    fi

    echo ""
    ok "All services running"
    echo -e "  ${CYAN}API:${NC}    http://localhost:8000"
    echo -e "  ${CYAN}Docs:${NC}   http://localhost:8000/docs"
    echo -e "  ${CYAN}Health:${NC} http://localhost:8000/health"
    echo ""
    echo -e "Press ${YELLOW}Ctrl+C${NC} or run ${YELLOW}./dev.sh stopall${NC} from another terminal"
    echo ""

    cd "$BACKEND_DIR"
    poetry run uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --log-level info &

    local pid=$!
    echo "$pid" > "$PID_FILE"

    trap 'echo ""; stop_uvicorn; exit 0' INT TERM
    wait "$pid"
    rm -f "$PID_FILE"
}

cmd_stopall() {
    stop_uvicorn
    stop_brew_service "redis"
    stop_brew_service "postgresql@15" 2>/dev/null || stop_brew_service "postgresql"
    ok "All services stopped"
}

# ── Entry point ───────────────────────────────────────────────────────────────

case "${1:-start}" in
    start)   cmd_start ;;
    stopall) cmd_stopall ;;
    *)
        echo "Usage: $0 [start|stopall]"
        echo "  start    — Start Redis, PostgreSQL, and Uvicorn (default)"
        echo "  stopall  — Stop Uvicorn, Redis, and PostgreSQL"
        exit 1
        ;;
esac
