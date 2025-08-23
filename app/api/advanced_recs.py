"""Advanced trading recommendation API.

This module exposes an endpoint that derives an advanced trading signal
from historical price data.  The advanced algorithm builds on the basic
EMA/RSI based approach by incorporating the MACD oscillator.  It
fetches candlestick data via the Binance service, computes MACD and RSI
values and uses simple thresholds to derive a trading recommendation.

The endpoint returns the latest values of the MACD line, its signal
line, the MACD histogram and the 14‑period RSI along with the computed
recommendation.  Errors encountered during data retrieval or
computation are returned as HTTP 400 responses with a descriptive
message.
"""

from fastapi import APIRouter, HTTPException, Query

from app.services import advanced_recommender


router = APIRouter(prefix="/api", tags=["advanced_recs"])


@router.get("/advanced_recommendations")
def advanced_recommendations(
    *,
    symbol: str = Query(..., examples=["BTCUSDT"]),
    interval: str = Query(..., examples=["1h"])
) -> dict[str, object]:
    """Return an advanced trading recommendation.

    Parameters
    ----------
    symbol:
        The trading pair symbol (for example ``BTCUSDT``).  Must be
        provided.
    interval:
        The candle interval (e.g. ``1h``, ``4h``, ``1d``).  Must be
        provided.

    Returns
    -------
    dict
        A dictionary containing the symbol, interval, last MACD value,
        MACD signal value, MACD histogram, RSI14 and the derived
        recommendation (``STRONG_BUY``, ``BUY``, ``HOLD``, ``SELL`` or
        ``STRONG_SELL``).
    """
    try:
        return advanced_recommender.advanced_recommendation(symbol, interval)
    except Exception as exc:
        # Wrap any underlying exception in a 400 so callers receive a
        # descriptive error message rather than an internal server error.
        raise HTTPException(400, f"advanced recs error: {exc}") from exc
