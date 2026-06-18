from fastapi import FastAPI

app = FastAPI(title="Karmine")


@app.get("/health")
def health():
    return {"status": "ok"}
