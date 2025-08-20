from fastapi import APIRouter, HTTPException, Query
from app.services import binance

router = APIRouter(prefix="/api", tags=["market"])

@router.get("/klines")
def get_klines(
    symbol: str = Query(..., examples=["BTCUSDT"]),
    interval: str = Query(..., examples=["1h"]),
    limit: int = Query(300, ge=1, le=1000)
):
    try:
        raw = binance.klines(symbol, interval, limit)
        # маппинг к формату фронта
        kl = [{
            "t": r[0],                  # open time (ms)
            "o": float(r[1]),
            "h": float(r[2]),
            "l": float(r[3]),
            "c": float(r[4])
        } for r in raw]
        return {"symbol": symbol, "interval": interval, "klines": kl}
    except Exception as e:
        raise HTTPException(400, f"klines error: {e}")
