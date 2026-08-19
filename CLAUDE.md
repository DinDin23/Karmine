# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Karmine: a peer-to-peer wagering platform for Clash Royale. Users deposit money, queue with a stake amount, get matched against another queued player at the same stake, play the match in-game, and the app settles the wager automatically by polling the Clash Royale API for the result.

FastAPI + SQLAlchemy + Postgres backend (`app/`), React + Vite frontend (`frontend/`), Alembic migrations.

## Commands

**Local dev (backend + frontend + Postgres together):**
```bash
./dev.sh start   # starts postgres (brew services), backend :8001, frontend :5173
./dev.sh status
./dev.sh stop
```
Logs land in `.dev-logs/`, pid files in `.dev-pids/`.

**Backend only:**
```bash
poetry install
poetry run uvicorn app.main:app --port 8001 --reload
```

**Migrations:**
```bash
poetry run alembic upgrade head
poetry run alembic revision --autogenerate -m "description"
```

**Frontend:**
```bash
cd frontend
npm run dev       # vite dev server
npm run build
npm run lint       # oxlint
```

**Seed fake data (test DB only):**
```bash
poetry run python scripts/seed_fake_data.py [--count N] [--reset]
```
Reads `.env.test`, not `.env`, and hard-refuses to run unless the target database name is `karmine_test` — this is the only guard against seeding the real database. Seeded users all share the password `password123`.

There is currently no automated test suite (no pytest config, no e2e tests despite Playwright being a frontend devDependency) — don't assume `pytest` or a test command exists.

## Environment

Config is loaded via `pydantic-settings` from `.env` (see `app/config.py` for the full list of required vars; `.env.example` documents them). Notable ones: `DATABASE_URL`, `JWT_SECRET`, `CR_API_KEY`/`CR_API_URL` (Clash Royale API), `TWILIO_*` (match-invite SMS), `SETTLEMENT_POLL_INTERVAL_SECONDS`, `MATCH_TIMEOUT_MINUTES`, `CORS_ALLOW_ORIGINS`.

Frontend talks to the backend via `VITE_API_BASE_URL` (`frontend/src/api.js`), defaulting to `http://127.0.0.1:8001` locally and set to `https://api.karmine.us` in `frontend/.env.production`.

## Architecture

**Money model:** there is no `balance` column anywhere. A user's balance is always the sum of their `Transaction` rows (`app/routers/wallet.py::get_balance`), recomputed on every read. Deposits/withdrawals/wager locks/payouts/refunds are all just signed `Transaction` rows tied to `TransactionType`. When touching money logic, add a transaction row rather than mutating a balance field.

**Matchmaking → wager lifecycle** (`app/routers/matchmaking.py`, `app/models/`):
1. `POST /matchmaking/queue` creates a `MatchmakingRequest` (status `WAITING`). If another `WAITING` request exists at the same `stake_amount` (and that opponent still has sufficient balance), the two requests are atomically matched into a `Wager` (status `MATCHED`), both requests flip to `MATCHED`, and a `WAGER_LOCK` transaction (negative amount) is created for each player. The opponent match uses `.with_for_update()` to avoid two simultaneous queuers double-matching the same request.
2. Both players are notified: a WebSocket push (`connection_manager`) to whoever was already connected, plus an SMS via Twilio (`sms_service`) with the opponent's Supercell friend link, sent to both.
3. Players play the match in Clash Royale itself — the app doesn't referee the game, only the money.
4. A background thread (`settlement_worker.start()`, launched from `app/main.py`'s lifespan) polls every `SETTLEMENT_POLL_INTERVAL_SECONDS` and calls `settlement_service.poll_and_settle()` + `expire_stale_wagers()` against every `MATCHED`/`AWAITING_RESULT` wager.
5. `settle_wager` fetches player1's CR battlelog (`cr_api_service.get_battlelog`) and looks for a `PvP` or `friendly` battle against player2 that started after the wager was created; crowns decide the winner, tower HP breaks a crown tie (overtime). If found, the wager is marked `SETTLED`, a `WAGER_PAYOUT` transaction (2x stake) is created for the winner, and both players get a WS push.
6. `expire_stale_wagers` cancels + refunds (`WAGER_REFUND` to both players) any wager still unsettled after `MATCH_TIMEOUT_MINUTES`.
7. `matchmaking_status.build_status_out` is the single place that assembles the per-viewer status payload (opponent id/link, wager status, winner) — used by the queue/status HTTP endpoints, the WS push on match, and the WS pushes from settlement. Keep it as the one source of truth for that shape rather than reassembling it elsewhere.

**Auth:** JWT bearer tokens (`app/core/security.py`, HS256, subject = user id). `get_current_user` (`app/dependencies.py`) is the standard dependency for protected routes. The matchmaking WebSocket can't use header-based auth, so it takes the token as a query param and decodes it manually (`app/routers/matchmaking.py::matchmaking_ws`).

**Real-time updates:** `connection_manager.py` keeps an in-memory `{user_id: WebSocket}` map. Because the settlement worker runs on a background *thread* while the WebSocket lives on the asyncio event loop, `notify()` is thread-safe and uses `asyncio.run_coroutine_threadsafe` against a loop captured at startup (`set_loop`, called from the FastAPI lifespan). This in-memory map means multi-process/multi-instance deployment would need a different mechanism (e.g. Redis pub/sub) — currently it only works because the backend runs as a single process.

## Deployment

Deploys to a Raspberry Pi over Tailscale SSH, triggered by `.github/workflows/deploy.yml` on every push to `main` (or manually via `workflow_dispatch`). The Pi's `authorized_keys` forces the deploy key to always run `scripts/deploy.sh`, ignoring whatever command is actually sent over SSH.

`scripts/deploy.sh` is diff-driven: it fast-forwards to `origin/main`, then only runs `poetry install` if `pyproject.toml`/`poetry.lock` changed, only runs `alembic upgrade head` + restarts `karmine-backend.service` if backend-relevant paths changed, and only runs `npm ci && npm run build` if `frontend/` changed (the frontend systemd service serves `dist/` directly, no restart needed). When changing deploy behavior, this script is the source of truth, not the workflow file.
