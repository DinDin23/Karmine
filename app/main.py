from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import auth, matchmaking, wallet, wager
from app.services import settlement_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    settlement_worker.start()
    yield
    settlement_worker.stop()


app = FastAPI(title="Karmine", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(wallet.router)
app.include_router(matchmaking.router)
app.include_router(wager.router)


@app.get("/health")
def health():
    return {"status": "ok"}
