from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine
from app.models.base import Base
from app.routers import auth, users
from app.utils.exceptions import AppException
from app.utils.redis_client import close_redis, init_redis

# Import all models so Base.metadata knows about them
import app.models.user  # noqa: F401
import app.models.match  # noqa: F401
import app.models.transaction  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    await init_redis()
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="CR Matchmaking API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


app.include_router(auth.router)
app.include_router(users.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
