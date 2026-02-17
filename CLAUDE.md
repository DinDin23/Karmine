# Karmine — CR Matchmaking Platform

## Project Overview

A Clash Royale wagering platform where users bet real money on 1v1 matches. Players queue up with a bet amount, get matched with an opponent of similar skill, play the battle in-game, and the system auto-verifies the result via the CR API and distributes funds.

---

## Repo Structure

```
Karmine/
├── cr-matchmaking-backend/     # FastAPI backend (active work)
│   ├── app/
│   │   ├── main.py             # App entry point, lifespan, exception handler, /health
│   │   ├── config.py           # All settings via pydantic-settings (.env)
│   │   ├── database.py         # Async SQLAlchemy engine + session factory
│   │   ├── models/             # SQLAlchemy ORM models
│   │   │   ├── user.py         # User + UserBalance
│   │   │   ├── match.py        # Match
│   │   │   └── transaction.py  # Transaction
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   │   ├── auth.py         # RegisterRequest, LoginRequest, AuthResponse
│   │   │   ├── user.py         # UserResponse, UserUpdate, CR linking/verify
│   │   │   ├── match.py        # MatchResponse, MatchDetailResponse
│   │   │   ├── matchmaking.py  # JoinQueueRequest/Response, QueueStatusResponse
│   │   │   └── balance.py      # BalanceResponse, DepositRequest/Response, etc.
│   │   └── utils/
│   │       ├── exceptions.py   # AppException hierarchy (7 custom exceptions)
│   │       └── redis_client.py # Redis init/close/DI dependency
│   ├── docs/
│   │   └── architecture.md     # Full Mermaid diagrams (ER, flows, built vs missing)
│   ├── .env.example
│   └── pyproject.toml          # Poetry — Python 3.11+
├── cr-matchmaking-frontend/    # React Native frontend (planned)
│   ├── src/
│   │   ├── screens/            # Screen components (Auth, Home, Matchmaking, Balance, etc.)
│   │   ├── components/         # Reusable UI components
│   │   ├── navigation/         # React Navigation stack/tab setup
│   │   ├── services/           # API client, WebSocket/SSE handlers
│   │   ├── store/              # State management (Zustand or Redux Toolkit)
│   │   ├── hooks/              # Custom React hooks
│   │   └── utils/              # Helpers, constants, types
│   ├── app.json                # Expo config
│   └── package.json
└── docs/
    └── architecture.md         # (same file, referenced above)
```

---

## Tech Stack — Backend

| Layer | Tech |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI 0.115 |
| ASGI server | Uvicorn (standard) |
| ORM | SQLAlchemy 2.0 async |
| DB driver | asyncpg |
| Database | PostgreSQL 15+ |
| Cache/Queue | Redis 7+ (hiredis) |
| Validation | Pydantic v2 + pydantic-settings |
| Auth | python-jose (JWT, HS256, 24h expiry) |
| Passwords | passlib + bcrypt |
| HTTP client | httpx (async) |
| Payments | Stripe SDK v12 |
| Package mgr | Poetry |
| Formatting | Black + isort |
| Linting | Ruff |
| Type check | Mypy |
| Tests | pytest + pytest-asyncio |

---

## Tech Stack — Frontend

| Layer | Tech |
|---|---|
| Framework | React Native (Expo) |
| Targets | Web, iOS, Android |
| Language | TypeScript |
| Navigation | React Navigation v7 |
| State | Zustand (or Redux Toolkit) |
| API client | Axios or fetch with typed wrappers |
| Real-time | WebSocket / SSE (match events, balance updates) |
| Payments | Stripe React Native SDK |
| Styling | NativeWind (Tailwind for RN) or StyleSheet |
| Package mgr | npm or yarn (Expo managed workflow) |

---

## What Has Been Built

- **`config.py`** — All env vars via pydantic-settings (DB, Redis, JWT, CR API, Stripe, platform rules)
- **`database.py`** — Async SQLAlchemy engine, `async_session` factory, `get_db()` DI dependency
- **`main.py`** — FastAPI app with lifespan (Redis init/close + engine dispose), global `AppException` handler, `GET /health`
- **`models/`** — `User`, `UserBalance`, `Match`, `Transaction` SQLAlchemy models with all columns/indexes
- **`schemas/`** — Full Pydantic v2 schemas for all domains (Auth, User, Match, Matchmaking, Balance)
- **`utils/exceptions.py`** — `AppException` base + 7 typed subclasses (`InsufficientBalance`, `AccountNotVerified`, `InvalidPlayerTag`, `MatchExpired`, `VerificationFailed`, `PaymentFailed`, `RateLimitExceeded`)
- **`utils/redis_client.py`** — `init_redis()`, `close_redis()`, `get_redis()` DI dependency

---

## What Still Needs Building

- **`app/routers/`** — `auth.py`, `users.py`, `matches.py`, `matchmaking.py`, `balance.py`, `webhooks.py`
- **`app/services/`** — `auth_service.py`, `user_service.py`, `match_service.py`, `matchmaking_service.py`, `payment_service.py`, `cr_api_service.py`
- **`app/dependencies.py`** — `get_current_user`, `require_verified_cr_account`
- **Alembic migrations** — Database schema migrations
- **Matchmaking algorithm** — Redis sorted-set queues (`queue:{betAmount}`), trophy-range expansion logic
- **Battle verification worker** — CR API polling every 10s, cross-validate both players' battle logs
- **Timeout worker** — Cancel/refund expired matches every 30s
- **Stripe integration** — PaymentIntent for deposits, payouts for withdrawals, webhook handler
- **Rate limiting middleware**
- **WebSocket / SSE** — Real-time match found / balance update events
- **Tests** — pytest + pytest-asyncio
- **Docker / docker-compose**
- **Frontend (`cr-matchmaking-frontend/`)** — React Native + Expo app (web, iOS, Android)
  - Auth screens (register, login)
  - Home / dashboard
  - Matchmaking queue UI with real-time status
  - Match history + detail views
  - Balance screen (deposit, withdraw, transaction history)
  - CR account linking + verification flow
  - Stripe payment sheet integration

---

## Key Business Rules

- **Platform fee:** 10% of total pot. Example: $10 bet each → $20 pot → $2 fee → $18 to winner
- **Escrow:** Funds move from `balance` → `escrowed` on queue join; released on match completion/cancellation
- **Match timeout:** 10 minutes. Both players refunded, no fee
- **Trophy range for matching:**
  - 0–30s wait: ±200 trophies
  - 30–60s wait: ±400 trophies
  - 60s+ wait: ±800 trophies
- **CR account verification:** Challenge-response — user adds a 5-digit code to their in-game name, system verifies via CR API. Code expires in 10 minutes.
- **Bet limits:** Min $1.00, Max $100.00
- **Deposit limits:** Min $5.00, Max $1000.00
- **Withdrawal min:** $10.00

---

## API Routes (Planned)

```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/refresh

GET    /api/users/me
PATCH  /api/users/me
GET    /api/users/me/stats
POST   /api/users/me/link-cr
POST   /api/users/me/verify-cr

POST   /api/matchmaking/queue
GET    /api/matchmaking/queue/status
DELETE /api/matchmaking/queue

GET    /api/matches
GET    /api/matches/{match_id}
POST   /api/matches/{match_id}/dispute

GET    /api/balance
POST   /api/balance/deposit
POST   /api/balance/withdraw
GET    /api/balance/transactions

POST   /api/webhooks/stripe
```

---

## Database Schema (Summary)

- **`users`** — user_id (PK), email, password_hash, username, cr_player_tag, cr_player_verified, trophy_level
- **`user_balances`** — user_id (PK/FK), balance, escrowed, lifetime_deposited/withdrawn/wagered/won
- **`matches`** — match_id, player1_id, player2_id, player tags (snapshot), bet_amount, status, winner_id, battle_time, expires_at
- **`transactions`** — transaction_id, user_id, type (deposit/withdraw/bet_placed/win/loss/refund), amount, balance_before/after, match_id, stripe_payment_id, status, metadata (JSONB)

---

## Redis Key Patterns

```
queue:{betAmount}           Sorted set — matchmaking queue per bet tier
match:{matchId}             Hash — active match cache (TTL 15min)
session:{token}             String JSON — user session cache (TTL 24h)
cr:battlelog:{playerTag}    String JSON — CR battle log cache (TTL 30s)
cr:player:{playerTag}       String JSON — CR player profile cache (TTL 5min)
```

---

## Environment Variables

See `cr-matchmaking-backend/.env.example` for the full list. Key vars:
- `DATABASE_URL` — postgresql+asyncpg://...
- `REDIS_URL` — redis://localhost:6379
- `JWT_SECRET` — signing key
- `CR_API_KEY` — Clash Royale API key
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- `PLATFORM_FEE_PERCENTAGE` — default 10.0

---

## Development Setup

```bash
cd cr-matchmaking-backend
poetry install
cp .env.example .env   # fill in values
poetry run uvicorn app.main:app --reload
```

Swagger UI available at `http://localhost:8000/docs`

---

## Architecture Reference

Full Mermaid diagrams (system arch, ER diagram, schema classes, exception hierarchy, module dependencies, sequence flows) are in `cr-matchmaking-backend/docs/architecture.md`.
