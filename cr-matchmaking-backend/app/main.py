from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import engine
from app.routers import auth
from app.utils.exceptions import AppException
from app.utils.redis_client import close_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    await init_redis()
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
