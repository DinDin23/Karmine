# CR Matchmaking Backend — Architecture Diagrams

> All diagrams use [Mermaid](https://mermaid.js.org/) syntax.
> View in VS Code (Mermaid extension), GitHub, or [mermaid.live](https://mermaid.live).

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Database ER Diagram](#2-database-er-diagram)
3. [Pydantic Schemas](#3-pydantic-schemas)
4. [Exception Hierarchy](#4-exception-hierarchy)
5. [File / Module Dependency Graph](#5-file--module-dependency-graph)
6. [Planned API Endpoints](#6-planned-api-endpoints)
7. [User Registration & CR Linking Flow](#7-user-registration--cr-linking-flow)
8. [Matchmaking Flow](#8-matchmaking-flow)
9. [Payment Flow](#9-payment-flow)
10. [App Lifespan](#10-app-lifespan)
11. [Configuration Map](#11-configuration-map)
12. [Built vs Missing](#12-built-vs-missing)

---

## 1. System Architecture

How the FastAPI application connects to its external dependencies.

```mermaid
graph TB
    Client["Client<br/>(React Frontend)"]

    subgraph FastAPI ["FastAPI Application"]
        Main["main.py<br/>Lifespan · Exception Handler · /health"]
        Routers["Routers<br/>(planned)"]
        Services["Service Layer<br/>(planned)"]
        Models["SQLAlchemy Models"]
        Schemas["Pydantic Schemas"]
        Exceptions["AppException Hierarchy"]
        Config["config.py<br/>Settings (env)"]
    end

    subgraph External ["External Services"]
        PG[("PostgreSQL<br/>(AsyncPG)")]
        Redis[("Redis<br/>(hiredis)")]
        StripeAPI["Stripe API"]
        CRAPI["Clash Royale API"]
    end

    Client -->|"HTTP / JSON"| Main
    Main --> Routers
    Routers --> Services
    Services --> Models
    Services --> Schemas
    Services --> Exceptions
    Models -->|"async_session"| PG
    Services -->|"get_redis()"| Redis
    Services -->|"stripe SDK"| StripeAPI
    Services -->|"httpx / aiohttp"| CRAPI
    Config -.->|"provides settings"| Main
    Config -.->|"DATABASE_URL"| PG
    Config -.->|"REDIS_URL"| Redis
    Config -.->|"STRIPE_SECRET_KEY"| StripeAPI
    Config -.->|"CR_API_KEY"| CRAPI

    style FastAPI fill:#1a1a2e,stroke:#e94560,color:#fff
    style External fill:#0f3460,stroke:#16213e,color:#fff
```

---

## 2. Database ER Diagram

All four tables with columns, types, keys, and relationships.

```mermaid
erDiagram
    users {
        UUID user_id PK
        VARCHAR_255 email UK "indexed"
        VARCHAR_255 password_hash
        VARCHAR_50 username UK
        VARCHAR_20 cr_player_tag UK "nullable, indexed"
        BOOLEAN cr_player_verified "default false"
        INTEGER trophy_level "nullable"
        TIMESTAMP created_at "server default"
        TIMESTAMP updated_at "on update"
    }

    user_balances {
        UUID user_id PK, FK "references users"
        NUMERIC_10_2 balance "default 0.00"
        NUMERIC_10_2 escrowed "default 0.00"
        NUMERIC_10_2 lifetime_deposited
        NUMERIC_10_2 lifetime_withdrawn
        NUMERIC_10_2 lifetime_wagered
        NUMERIC_10_2 lifetime_won
        TIMESTAMP updated_at "on update"
    }

    matches {
        UUID match_id PK
        UUID player1_id FK "references users"
        UUID player2_id FK "references users"
        VARCHAR_20 player1_tag "snapshot"
        VARCHAR_20 player2_tag "snapshot"
        NUMERIC_10_2 bet_amount
        VARCHAR_20 status "active|completed|cancelled|disputed"
        UUID winner_id FK "nullable, references users"
        TIMESTAMP battle_time "nullable"
        TIMESTAMP created_at "server default"
        TIMESTAMP expires_at "partial index on active"
        TIMESTAMP completed_at "nullable"
        VARCHAR_100 cancellation_reason "nullable"
    }

    transactions {
        UUID transaction_id PK
        UUID user_id FK "references users, indexed"
        VARCHAR_50 type "deposit|withdraw|bet_placed|win|loss|refund"
        NUMERIC_10_2 amount
        NUMERIC_10_2 balance_before "nullable"
        NUMERIC_10_2 balance_after "nullable"
        UUID match_id FK "nullable, references matches, indexed"
        VARCHAR_100 stripe_payment_id "nullable"
        VARCHAR_20 status "pending|completed|failed"
        JSONB metadata "arbitrary JSON"
        TIMESTAMP created_at "server default, indexed"
    }

    users ||--|| user_balances : "has one"
    users ||--o{ matches : "plays as player1"
    users ||--o{ matches : "plays as player2"
    users ||--o{ matches : "wins"
    users ||--o{ transactions : "owns"
    matches ||--o{ transactions : "linked to"
```

---

## 3. Pydantic Schemas

All request/response contracts grouped by domain.

```mermaid
classDiagram
    direction LR

    namespace Auth {
        class RegisterRequest {
            +EmailStr email
            +str password "8-128 chars"
            +str username "3-50 chars"
        }
        class LoginRequest {
            +EmailStr email
            +str password
        }
        class TokenResponse {
            +str token
        }
        class AuthResponse {
            +str token
            +UserResponse user
        }
    }

    namespace User {
        class UserResponse {
            +UUID user_id
            +str email
            +str username
            +str|None cr_player_tag
            +bool cr_player_verified
            +int|None trophy_level
        }
        class UserUpdate {
            +str|None username
            +str|None email
        }
        class LinkCRAccountRequest {
            +str player_tag "regex #[A-Z0-9]+"
        }
        class VerifyCRAccountRequest {
            +str verification_code "5 chars"
        }
        class VerifyCRAccountResponse {
            +bool verified
            +str player_tag
            +str player_name
            +int trophy_level
        }
        class UserStatsResponse {
            +int total_matches
            +int wins
            +int losses
            +int draws
            +float win_rate
            +Decimal lifetime_wagered
            +Decimal lifetime_won
        }
    }

    namespace Match {
        class OpponentInfo {
            +str username
            +str player_tag
            +int trophy_level
        }
        class PlayerInfo {
            +UUID user_id
            +str username
            +str player_tag
            +int trophy_level
        }
        class MatchResponse {
            +UUID match_id
            +OpponentInfo opponent
            +Decimal bet_amount
            +str status
            +str|None result
            +Decimal|None payout
            +datetime created_at
            +datetime|None completed_at
        }
        class MatchDetailResponse {
            +UUID match_id
            +PlayerInfo player1
            +PlayerInfo player2
            +Decimal bet_amount
            +str status
            +UUID|None winner_id
            +datetime|None battle_time
            +datetime created_at
            +datetime expires_at
            +datetime|None completed_at
        }
        class MatchListResponse {
            +list~MatchResponse~ matches
            +int total
        }
        class DisputeRequest {
            +str reason
        }
    }

    namespace Matchmaking {
        class JoinQueueRequest {
            +float bet_amount "gt 0"
        }
        class JoinQueueResponse {
            +str queue_id
            +int position
            +str estimated_wait_time
        }
        class QueueStatusResponse {
            +bool in_queue
            +float|None bet_amount
            +int|None queue_position
            +str|None wait_time
        }
        class MatchFoundEvent {
            +UUID match_id
            +OpponentInfo opponent
            +Decimal bet_amount
            +datetime expires_at
        }
    }

    namespace Balance {
        class BalanceResponse {
            +Decimal balance
            +Decimal escrowed
            +Decimal available "computed"
            +Decimal lifetime_deposited
            +Decimal lifetime_withdrawn
            +Decimal lifetime_won
        }
        class DepositRequest {
            +float amount "0 lt amount le 1000"
            +str payment_method_id
        }
        class DepositResponse {
            +UUID transaction_id
            +Decimal amount
            +Decimal new_balance
            +str status
        }
        class WithdrawRequest {
            +float amount "gt 0"
        }
        class WithdrawResponse {
            +UUID transaction_id
            +Decimal amount
            +Decimal new_balance
            +str status
        }
        class TransactionResponse {
            +UUID transaction_id
            +str type
            +Decimal amount
            +Decimal|None balance_before
            +Decimal|None balance_after
            +UUID|None match_id
            +str status
            +datetime created_at
        }
    }

    AuthResponse --> UserResponse
    MatchResponse --> OpponentInfo
    MatchDetailResponse --> PlayerInfo
    MatchFoundEvent --> OpponentInfo
```

---

## 4. Exception Hierarchy

Custom exception tree with HTTP status codes and error codes.

```mermaid
classDiagram
    direction TB

    class Exception {
        <<built-in>>
    }

    class AppException {
        +str code
        +str message
        +int status_code
        +dict details
    }

    class InsufficientBalance {
        code = "INSUFFICIENT_BALANCE"
        status_code = 400
        details: available, required
    }

    class AccountNotVerified {
        code = "ACCOUNT_NOT_VERIFIED"
        status_code = 403
    }

    class InvalidPlayerTag {
        code = "INVALID_PLAYER_TAG"
        status_code = 404
        details: player_tag
    }

    class MatchExpired {
        code = "MATCH_EXPIRED"
        status_code = 410
        details: match_id
    }

    class VerificationFailed {
        code = "VERIFICATION_FAILED"
        status_code = 400
        details: reason
    }

    class PaymentFailed {
        code = "PAYMENT_FAILED"
        status_code = 402
        details: reason
    }

    class RateLimitExceeded {
        code = "RATE_LIMIT_EXCEEDED"
        status_code = 429
    }

    Exception <|-- AppException
    AppException <|-- InsufficientBalance
    AppException <|-- AccountNotVerified
    AppException <|-- InvalidPlayerTag
    AppException <|-- MatchExpired
    AppException <|-- VerificationFailed
    AppException <|-- PaymentFailed
    AppException <|-- RateLimitExceeded
```

---

## 5. File / Module Dependency Graph

How every source file imports from others.

```mermaid
graph TD
    subgraph app ["app/"]
        main["main.py"]
        config["config.py"]
        database["database.py"]
    end

    subgraph models ["app/models/"]
        models_init["__init__.py"]
        base["base.py"]
        user_model["user.py"]
        match_model["match.py"]
        transaction_model["transaction.py"]
    end

    subgraph schemas ["app/schemas/"]
        schemas_init["__init__.py"]
        auth_schema["auth.py"]
        user_schema["user.py"]
        match_schema["match.py"]
        matchmaking_schema["matchmaking.py"]
        balance_schema["balance.py"]
    end

    subgraph utils ["app/utils/"]
        exceptions["exceptions.py"]
        redis_client["redis_client.py"]
    end

    %% config is the root dependency
    database --> config
    redis_client --> config

    %% main.py imports
    main --> database
    main --> exceptions
    main --> redis_client

    %% model imports
    user_model --> base
    match_model --> base
    transaction_model --> base
    models_init --> user_model
    models_init --> match_model
    models_init --> transaction_model

    %% schema imports
    auth_schema --> user_schema
    matchmaking_schema --> match_schema
    schemas_init --> auth_schema
    schemas_init --> user_schema
    schemas_init --> match_schema
    schemas_init --> matchmaking_schema
    schemas_init --> balance_schema

    %% External libraries (dimmed)
    pydantic_settings["pydantic_settings"]:::ext
    sqlalchemy["sqlalchemy"]:::ext
    redis_lib["redis.asyncio"]:::ext
    fastapi["fastapi"]:::ext

    config --> pydantic_settings
    database --> sqlalchemy
    base --> sqlalchemy
    redis_client --> redis_lib
    main --> fastapi

    classDef ext fill:#555,stroke:#777,color:#ccc,stroke-dasharray: 5 5
```

---

## 6. Planned API Endpoints

Full REST API surface area derived from schemas and domain design.

```mermaid
graph LR
    subgraph Health
        H1["GET /health"]
    end

    subgraph Auth ["/api/auth"]
        A1["POST /register"]
        A2["POST /login"]
        A3["POST /refresh"]
    end

    subgraph Users ["/api/users"]
        U1["GET /me"]
        U2["PATCH /me"]
        U3["GET /me/stats"]
        U4["POST /me/link-cr"]
        U5["POST /me/verify-cr"]
    end

    subgraph Matchmaking ["/api/matchmaking"]
        M1["POST /queue"]
        M2["GET /queue/status"]
        M3["DELETE /queue"]
    end

    subgraph Matches ["/api/matches"]
        MA1["GET /"]
        MA2["GET /{match_id}"]
        MA3["POST /{match_id}/dispute"]
    end

    subgraph Balance ["/api/balance"]
        B1["GET /"]
        B2["POST /deposit"]
        B3["POST /withdraw"]
        B4["GET /transactions"]
    end

    subgraph Stripe ["/api/webhooks"]
        S1["POST /stripe"]
    end

    H1 ---|"200 status ok"| Health
    A1 ---|"RegisterRequest -> AuthResponse"| Auth
    A2 ---|"LoginRequest -> AuthResponse"| Auth
    A3 ---|"-> TokenResponse"| Auth
    U1 ---|"-> UserResponse"| Users
    U2 ---|"UserUpdate -> UserResponse"| Users
    U3 ---|"-> UserStatsResponse"| Users
    U4 ---|"LinkCRAccountRequest"| Users
    U5 ---|"VerifyCRAccountRequest -> VerifyCRAccountResponse"| Users
    M1 ---|"JoinQueueRequest -> JoinQueueResponse"| Matchmaking
    M2 ---|"-> QueueStatusResponse"| Matchmaking
    MA1 ---|"-> MatchListResponse"| Matches
    MA2 ---|"-> MatchDetailResponse"| Matches
    MA3 ---|"DisputeRequest"| Matches
    B1 ---|"-> BalanceResponse"| Balance
    B2 ---|"DepositRequest -> DepositResponse"| Balance
    B3 ---|"WithdrawRequest -> WithdrawResponse"| Balance
```

---

## 7. User Registration & CR Linking Flow

Sequence diagram covering signup through Clash Royale account verification.

```mermaid
sequenceDiagram
    actor User
    participant FE as React Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant CR as Clash Royale API

    Note over User,CR: Registration
    User->>FE: Fill signup form
    FE->>API: POST /api/auth/register<br/>{email, password, username}
    API->>API: Hash password (bcrypt)
    API->>DB: INSERT users + user_balances
    DB-->>API: User record
    API->>API: Generate JWT
    API-->>FE: AuthResponse {token, user}
    FE-->>User: Dashboard

    Note over User,CR: Link Clash Royale Account
    User->>FE: Enter player tag (#ABC123)
    FE->>API: POST /api/users/me/link-cr<br/>{player_tag: "#ABC123"}
    API->>CR: GET /v1/players/%23ABC123
    CR-->>API: Player profile (name, trophies)
    API->>DB: UPDATE users SET cr_player_tag
    API-->>FE: 200 OK

    Note over User,CR: Verify Ownership
    User->>FE: Enter verification code
    FE->>API: POST /api/users/me/verify-cr<br/>{verification_code: "ABCDE"}
    API->>CR: GET /v1/players/%23ABC123
    CR-->>API: Player profile + description
    API->>API: Check code in player bio/description
    alt Code matches
        API->>DB: UPDATE users SET cr_player_verified=true, trophy_level=N
        API-->>FE: VerifyCRAccountResponse {verified: true}
        FE-->>User: Account verified!
    else Code does not match
        API-->>FE: VerificationFailed
        FE-->>User: Verification failed
    end
```

---

## 8. Matchmaking Flow

Full lifecycle: queue entry, match creation, battle, verification, and payout.

```mermaid
sequenceDiagram
    actor P1 as Player 1
    actor P2 as Player 2
    participant API as FastAPI
    participant Redis as Redis Queue
    participant DB as PostgreSQL
    participant CR as Clash Royale API

    Note over P1,CR: Join Queue
    P1->>API: POST /api/matchmaking/queue<br/>{bet_amount: 5.00}
    API->>API: Validate: verified account,<br/>sufficient balance
    API->>Redis: ZADD matchmaking_queue<br/>(trophy_level as score)
    API-->>P1: JoinQueueResponse {position, wait_time}

    P2->>API: POST /api/matchmaking/queue<br/>{bet_amount: 5.00}
    API->>Redis: ZADD matchmaking_queue

    Note over P1,CR: Match Found
    API->>Redis: Scan queue for compatible<br/>bet + trophy range
    Redis-->>API: P1, P2 matched
    API->>Redis: ZREM both players
    API->>DB: BEGIN TRANSACTION
    API->>DB: UPDATE user_balances<br/>balance -= 5.00, escrowed += 5.00<br/>(both players)
    API->>DB: INSERT matches<br/>{player1, player2, bet=5.00,<br/>status=active, expires_at}
    API->>DB: INSERT transactions x2<br/>{type=bet_placed, amount=5.00}
    API->>DB: COMMIT
    API-->>P1: MatchFoundEvent {match_id, opponent}
    API-->>P2: MatchFoundEvent {match_id, opponent}

    Note over P1,CR: Battle & Verification
    P1->>P2: Play Clash Royale battle (in-game)

    loop Poll for result
        API->>CR: GET /v1/players/{tag}/battlelog
        CR-->>API: Recent battles
        API->>API: Find battle between<br/>P1 tag and P2 tag
    end

    alt P1 wins
        API->>DB: BEGIN TRANSACTION
        API->>DB: UPDATE matches SET<br/>status=completed, winner=P1
        API->>API: Calculate payout<br/>pot=10.00, fee=10%=1.00, payout=9.00
        API->>DB: UPDATE P1 balance<br/>escrowed -= 5.00, balance += 9.00
        API->>DB: UPDATE P2 balance<br/>escrowed -= 5.00
        API->>DB: INSERT transactions<br/>(P1: win +9.00, P2: loss -5.00)
        API->>DB: COMMIT
        API-->>P1: Match result: WIN (+9.00)
        API-->>P2: Match result: LOSS (-5.00)
    else Match expires (no battle)
        API->>DB: UPDATE matches SET<br/>status=cancelled
        API->>DB: Refund escrow to both players
        API->>DB: INSERT transactions x2<br/>{type=refund}
        API-->>P1: Match cancelled (refund)
        API-->>P2: Match cancelled (refund)
    end
```

---

## 9. Payment Flow

Deposit and withdrawal sequences with Stripe integration.

```mermaid
sequenceDiagram
    actor User
    participant FE as React Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Stripe as Stripe API

    Note over User,Stripe: Deposit Flow
    User->>FE: Enter amount ($20.00)
    FE->>API: POST /api/balance/deposit<br/>{amount: 20.00, payment_method_id: "pm_xxx"}
    API->>Stripe: Create PaymentIntent<br/>{amount: 2000, currency: usd,<br/>payment_method: "pm_xxx",<br/>confirm: true}
    alt Payment succeeds
        Stripe-->>API: PaymentIntent {status: succeeded, id: "pi_xxx"}
        API->>DB: BEGIN TRANSACTION
        API->>DB: UPDATE user_balances<br/>balance += 20.00,<br/>lifetime_deposited += 20.00
        API->>DB: INSERT transactions<br/>{type=deposit, amount=20.00,<br/>stripe_payment_id="pi_xxx",<br/>status=completed}
        API->>DB: COMMIT
        API-->>FE: DepositResponse {new_balance: 20.00}
        FE-->>User: Deposit successful!
    else Payment fails
        Stripe-->>API: Error
        API-->>FE: PaymentFailed
        FE-->>User: Payment failed
    end

    Note over User,Stripe: Withdrawal Flow
    User->>FE: Request withdrawal ($15.00)
    FE->>API: POST /api/balance/withdraw<br/>{amount: 15.00}
    API->>API: Check balance >= 15.00
    alt Sufficient balance
        API->>Stripe: Create Transfer / Payout<br/>{amount: 1500}
        Stripe-->>API: Transfer succeeded
        API->>DB: BEGIN TRANSACTION
        API->>DB: UPDATE user_balances<br/>balance -= 15.00,<br/>lifetime_withdrawn += 15.00
        API->>DB: INSERT transactions<br/>{type=withdraw, amount=15.00,<br/>status=completed}
        API->>DB: COMMIT
        API-->>FE: WithdrawResponse {new_balance: 5.00}
        FE-->>User: Withdrawal processing!
    else Insufficient balance
        API-->>FE: InsufficientBalance {available, required}
        FE-->>User: Not enough funds
    end

    Note over User,Stripe: Stripe Webhook (async confirmation)
    Stripe->>API: POST /api/webhooks/stripe<br/>(payment_intent.succeeded)
    API->>API: Verify webhook signature
    API->>DB: Update transaction status<br/>if still pending
    API-->>Stripe: 200 OK
```

---

## 10. App Lifespan

Startup and shutdown sequence for the FastAPI application.

```mermaid
sequenceDiagram
    participant Uvicorn
    participant App as FastAPI App
    participant Redis as Redis Client
    participant DB as SQLAlchemy Engine

    Note over Uvicorn,DB: Startup
    Uvicorn->>App: Start ASGI app
    App->>App: lifespan() context manager enters

    App->>Redis: init_redis()
    Redis->>Redis: from_url(REDIS_URL,<br/>decode_responses=True)
    Redis-->>App: Redis client ready

    App->>App: yield (app is now serving)

    Note over Uvicorn,DB: Serving Requests
    Uvicorn->>App: Incoming HTTP requests
    App->>App: Route to handlers
    App->>Redis: get_redis() dependency
    App->>DB: get_db() dependency<br/>(async_session)

    Note over Uvicorn,DB: Shutdown
    Uvicorn->>App: SIGTERM / SIGINT
    App->>App: lifespan() context manager exits

    App->>Redis: close_redis()
    Redis->>Redis: aclose()
    Redis-->>App: Connection closed

    App->>DB: engine.dispose()
    DB->>DB: Close connection pool
    DB-->>App: Engine disposed

    App-->>Uvicorn: Shutdown complete
```

---

## 11. Configuration Map

All settings grouped by category with defaults.

```mermaid
mindmap
    root((Settings))
        Server
            DEBUG = False
            HOST = "0.0.0.0"
            PORT = 8000
        Database
            DATABASE_URL
                postgresql+asyncpg://
                user:pass@localhost/cr_matchmaking
        Redis
            REDIS_URL
                redis://localhost:6379
        JWT Auth
            JWT_SECRET
            JWT_ALGORITHM = "HS256"
            JWT_EXPIRATION_HOURS = 24
        Clash Royale API
            CR_API_KEY
            CR_API_URL
                https://api.clashroyale.com/v1
        Stripe Payments
            STRIPE_SECRET_KEY
            STRIPE_PUBLISHABLE_KEY
            STRIPE_WEBHOOK_SECRET
        Platform Rules
            PLATFORM_FEE_PERCENTAGE = 10.0%
            MATCH_TIMEOUT_MINUTES = 10
            MIN_BET_AMOUNT = 1.0
            MAX_BET_AMOUNT = 100.0
        Rate Limiting
            RATE_LIMIT_REQUESTS = 100
            RATE_LIMIT_PERIOD = 60s
```

---

## 12. Built vs Missing

Current project completion status.

```mermaid
graph TB
    subgraph Built ["Built"]
        direction TB
        C1["config.py<br/>All settings via .env"]
        C2["database.py<br/>Async SQLAlchemy engine + session"]
        C3["main.py<br/>Lifespan, exception handler, /health"]
        C4["models/<br/>User, UserBalance, Match, Transaction"]
        C5["schemas/<br/>Auth, User, Match, Matchmaking, Balance"]
        C6["utils/exceptions.py<br/>7 custom exception classes"]
        C7["utils/redis_client.py<br/>Init, close, DI dependency"]
    end

    subgraph Missing ["Missing"]
        direction TB
        M1["routers/<br/>Auth, Users, Matches,<br/>Matchmaking, Balance, Webhooks"]
        M2["services/<br/>Auth, User, Match,<br/>Matchmaking, Payment, CR API"]
        M3["dependencies/<br/>get_current_user, require_verified"]
        M4["Alembic migrations"]
        M5["Matchmaking algorithm<br/>(Redis sorted-set queue)"]
        M6["Battle verification<br/>(CR API polling)"]
        M7["Stripe integration logic"]
        M8["Rate limiting middleware"]
        M9["WebSocket / SSE<br/>for real-time events"]
        M10["Tests<br/>(pytest + pytest-asyncio)"]
        M11["Docker / docker-compose"]
    end

    style Built fill:#1b4332,stroke:#2d6a4f,color:#d8f3dc
    style Missing fill:#641220,stroke:#a4161a,color:#ffd6d6
```

---

*Generated for the CR Matchmaking Backend project.*
