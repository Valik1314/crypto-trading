from fastapi import APIRouter, HTTPException, Query
from app.services import binance, indicators

router = APIRouter(prefix="/api", tags=["recs"])

@router.get("/recommendations")
def recommendations(
    symbol: str = Query(..., examples=["BTCUSDT"]),
    interval: str = Query(..., examples=["1h"])
):
    try:
        raw = binance.klines(symbol, interval, 300)
        closes = [float(r[4]) for r in raw]
        ema12 = indicators.ema(closes, 12)
        ema26 = indicators.ema(closes, 26)
        rsi14 = indicators.rsi(closes, 14)

        last = len(closes) - 1
        sig = "HOLD"
        if ema12[last] and ema26[last]:
            if ema12[last] > ema26[last] and (not rsi14[last] or rsi14[last] < 70): sig = "BUY"
            if ema12[last] < ema26[last] and (not rsi14[last] or rsi14[last] > 30): sig = "SELL"

        return {
            "symbol": symbol,
            "interval": interval,
            "ema12": ema12[last],
            "ema26": ema26[last],
            "rsi14": rsi14[last],
            "signal": sig
        }
    except Exception as e:
        raise HTTPException(400, f"recs error: {e}")
