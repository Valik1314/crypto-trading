"""Market data API.

This module exposes endpoints for retrieving historical candlestick data
directly from the Binance API.  It wraps the lower–level ``app.services``
functions and translates their output into a format consumable by the
frontend.  Any exceptions thrown by the underlying service are captured
and returned as HTTP 400 errors with a descriptive message.
"""

from fastapi import APIRouter, HTTPException, Query

from app.services import binance


router = APIRouter(prefix="/api", tags=["market"])


@router.get("/klines")
def get_klines(
    *,
    symbol: str = Query(..., examples=["BTCUSDT"]),
    interval: str = Query(..., examples=["1h"]),
    limit: int = Query(300, ge=1, le=1000)
) -> dict[str, object]:
    """Retrieve historical candlestick data for a trading pair.

    Parameters
    ----------
    symbol:
        The trading pair symbol (e.g. ``BTCUSDT``).  Must be provided.
    interval:
        The candle interval (e.g. ``1h``, ``4h``, ``1d``).  Must be
        provided.
    limit:
        The maximum number of candles to return.  Defaults to 300 and
        must fall between 1 and 1000.

    Returns
    -------
    dict
        A JSON serialisable dictionary containing the original symbol,
        interval and an array of candles each with open time, open,
        high, low and close values.
    """
    try:
        raw = binance.klines(symbol, interval, limit)
        # Map raw Binance output to a format expected by the frontend
        kl = [
            {
                "t": r[0],  # open time in milliseconds
                "o": float(r[1]),
                "h": float(r[2]),
                "l": float(r[3]),
                "c": float(r[4]),
            }
            for r in raw
        ]
        return {"symbol": symbol, "interval": interval, "klines": kl}
    except Exception as exc:  # pragma: no cover - network errors mapped to HTTP
        raise HTTPException(400, f"klines error: {exc}") from exc
