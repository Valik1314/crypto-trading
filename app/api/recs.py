"""Trading recommendation API.

This module exposes an endpoint that derives a simple trading signal from
historical price data using exponential moving averages (EMAs) and the
relative strength index (RSI).  The implementation intentionally
mirrors the underlying indicator functions in ``app.services.indicators``
and makes no remote calls outside of the Binance klines endpoint.
"""

from fastapi import APIRouter, HTTPException, Query

from app.services import binance, indicators


router = APIRouter(prefix="/api", tags=["recs"])


@router.get("/recommendations")
def recommendations(
    *,
    symbol: str = Query(..., examples=["BTCUSDT"]),
    interval: str = Query(..., examples=["1h"])
) -> dict[str, object]:
    """Return a trading recommendation based on EMA and RSI.

    This endpoint fetches 300 candlesticks for the requested symbol and
    interval, computes two exponential moving averages (EMA‑12 and
    EMA‑26) along with a 14‑period RSI.  The signal is set to ``BUY``
    when the fast EMA crosses above the slow EMA and RSI is below 70,
    ``SELL`` when the fast EMA crosses below the slow EMA and RSI is
    above 30, otherwise ``HOLD``.

    Returns a dictionary containing the latest values of each indicator
    and the derived signal.  In the event of an error the API returns
    HTTP 400 with a description.
    """
    try:
        raw = binance.klines(symbol, interval, 300)
        closes = [float(r[4]) for r in raw]
        ema12 = indicators.ema(closes, 12)
        ema26 = indicators.ema(closes, 26)
        rsi14 = indicators.rsi(closes, 14)
        last = len(closes) - 1
        sig = "HOLD"
        # Only generate a signal if both EMA series have a value at the end
        if ema12[last] is not None and ema26[last] is not None:
            if ema12[last] > ema26[last] and (
                rsi14[last] is None or rsi14[last] < 70
            ):
                sig = "BUY"
            if ema12[last] < ema26[last] and (
                rsi14[last] is None or rsi14[last] > 30
            ):
                sig = "SELL"
        return {
            "symbol": symbol,
            "interval": interval,
            "ema12": ema12[last],
            "ema26": ema26[last],
            "rsi14": rsi14[last],
            "signal": sig,
        }
    except Exception as exc:
        raise HTTPException(400, f"recs error: {exc}") from exc
