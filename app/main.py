from fastapi import FastAPI

from app.routers import auth, wallet

app = FastAPI(title="Karmine")

app.include_router(auth.router)
app.include_router(wallet.router)


@app.get("/health")
def health():
    return {"status": "ok"}
