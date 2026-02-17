from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Server
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cr_matchmaking"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Clash Royale API
    CR_API_KEY: str = ""
    CR_API_URL: str = "https://api.clashroyale.com/v1"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Platform Settings
    PLATFORM_FEE_PERCENTAGE: float = 10.0
    MATCH_TIMEOUT_MINUTES: int = 10
    MIN_BET_AMOUNT: float = 1.0
    MAX_BET_AMOUNT: float = 100.0

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60


settings = Settings()
