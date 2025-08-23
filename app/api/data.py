"""OHLCV data API.

This module exposes endpoints for retrieving and normalising candlestick
data from exchanges using the ccxt library.  The data service supports
timeframe resampling, caching and gap filling so that downstream
consumers receive continuous time series.  When an error occurs the
endpoint raises HTTP 400 with a descriptive message.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services.data.ccxt_client import fetch_ohlcv
from app.services.data.cache import cached
from app.services.data.resampler import resample_ohlcv
from app.services.data.gaps import fill_gaps


router = APIRouter(prefix="/api/market", tags=["ohlcv"])


@router.get("/ohlcv")
def get_ohlcv(
    *,
    symbol: str = Query(..., examples=["BTC/USDT"]),
    tf: str = Query(..., examples=["1h"], alias="tf"),
    limit: int = Query(500, ge=1, le=1000),
) -> dict[str, object]:
    """Retrieve normalised OHLCV data for a trading pair.

    Parameters
    ----------
    symbol:
        Trading pair in ``BASE/QUOTE`` notation (e.g. ``BTC/USDT``).  Must be
        provided.
    tf:
        Desired timeframe (e.g. ``1h``, ``4h``).  Must be supported by
        ccxt and present in the timeframe mapping.
    limit:
        Maximum number of raw candles to fetch from the exchange.  Higher
        values may be truncated by the exchange.

    Returns
    -------
    dict
        A JSON serialisable dictionary containing the symbol, timeframe and
        an array of candles each with ``t`` (timestamp in milliseconds),
        ``o`` (open), ``h`` (high), ``l`` (low), ``c`` (close) and ``v``
        (volume).
    """
    try:
        # Fetch raw OHLCV data with caching.  The cached decorator ensures
        # that repeated calls for the same (symbol, tf, limit) return
        # quickly.
        @cached
        def _fetch(symbol: str, tf: str, limit: int):
            return fetch_ohlcv(symbol, tf, limit=limit)
        raw_df = _fetch(symbol, tf, limit)
        # Resample to requested timeframe.  This is a no‑op when the
        # timeframe matches the exchange's native interval.
        rs_df = resample_ohlcv(raw_df, tf)
        # Fill any missing candles
        full_df = fill_gaps(rs_df, timeframe=tf)
        candles = [
            {
                "t": int(row["timestamp"].to_pydatetime().timestamp() * 1000),
                "o": float(row["open"]),
                "h": float(row["high"]),
                "l": float(row["low"]),
                "c": float(row["close"]),
                "v": float(row["volume"]),
            }
            for _, row in full_df.iterrows()
        ]
        return {
            "symbol": symbol,
            "timeframe": tf,
            "candles": candles,
        }
    except Exception as exc:
        raise HTTPException(400, f"ohlcv error: {exc}") from exc
