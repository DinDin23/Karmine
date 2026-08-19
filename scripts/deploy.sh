#!/usr/bin/env bash
# Deploys the latest `main` to this Pi: pulls, runs migrations/deps only if
# needed, and restarts/rebuilds only the services whose inputs actually
# changed. Invoked over SSH by .github/workflows/deploy.yml (as a forced
# command in authorized_keys), so it can't assume an interactive shell's PATH
# or working directory.
set -euo pipefail

export PATH="/home/dindin23/.local/bin:/home/dindin23/.nvm/versions/node/v22.23.2/bin:/usr/bin:/bin:$PATH"

REPO_DIR="/home/dindin23/PersonalProjects/Karmine"
VENV_BIN="/home/dindin23/.cache/pypoetry/virtualenvs/karmine-teQBLjnL-py3.13/bin"

log() { echo "[deploy $(date -Iseconds)] $*"; }

cd "$REPO_DIR"

OLD_HEAD=$(git rev-parse HEAD)
log "current HEAD: $OLD_HEAD"

git fetch origin main
REMOTE_HEAD=$(git rev-parse origin/main)

if [ "$OLD_HEAD" != "$REMOTE_HEAD" ]; then
    log "fast-forwarding to origin/main ($REMOTE_HEAD)"
    git merge --ff-only origin/main
fi

NEW_HEAD=$(git rev-parse HEAD)

if [ "$OLD_HEAD" = "$NEW_HEAD" ]; then
    log "already up to date, nothing to deploy"
    exit 0
fi

log "deploying $OLD_HEAD -> $NEW_HEAD"
CHANGED=$(git diff --name-only "$OLD_HEAD" "$NEW_HEAD")
log "changed paths:"
echo "$CHANGED" | sed 's/^/  /'

if echo "$CHANGED" | grep -qE '^(pyproject\.toml|poetry\.lock)$'; then
    log "dependency files changed -- running poetry install"
    poetry install
fi

BACKEND_CHANGED=false
if echo "$CHANGED" | grep -qE '^(app/|alembic/|pyproject\.toml|poetry\.lock)'; then
    BACKEND_CHANGED=true
fi

if [ "$BACKEND_CHANGED" = true ]; then
    log "backend-relevant change -- running alembic migrations"
    "$VENV_BIN/alembic" upgrade head

    log "restarting karmine-backend.service"
    sudo systemctl restart karmine-backend.service
    sudo systemctl --no-pager --full status karmine-backend.service | head -5
fi

if echo "$CHANGED" | grep -qE '^frontend/'; then
    log "frontend changed -- rebuilding"
    cd "$REPO_DIR/frontend"
    npm ci
    npm run build
    log "frontend rebuilt (karmine-frontend.service serves dist/ live, no restart needed)"
fi

log "deploy complete ($OLD_HEAD -> $NEW_HEAD)"
