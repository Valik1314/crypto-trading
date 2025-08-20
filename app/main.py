from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.market import router as market_router
from app.api.recs import router as recs_router
from app.api.portfolio import router as portfolio_router

app = FastAPI(title="Personal Binance Spot Trader", version="1.0.0")

# API
app.include_router(market_router)
app.include_router(recs_router)
app.include_router(portfolio_router)

@app.get("/api/health")
def health():
    return {"ok": True}

# Статика (фронт)
app.mount("/", StaticFiles(directory="web", html=True), name="web")
