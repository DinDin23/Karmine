import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, matchmaking, wallet, wager
from app.services import connection_manager, settlement_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection_manager.set_loop(asyncio.get_running_loop())
    settlement_worker.start()
    yield
    settlement_worker.stop()


app = FastAPI(title="Karmine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(wallet.router)
app.include_router(matchmaking.router)
app.include_router(wager.router)


@app.get("/health")
def health():
    return {"status": "ok"}
