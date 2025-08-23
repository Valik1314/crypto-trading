"""Advanced trading recommendation engine.

This module implements a more nuanced trading signal than the basic
recommendation logic found in the original project.  It combines the
Moving Average Convergence Divergence (MACD) oscillator with the RSI
indicator to classify momentum and market conditions.  The result
produces one of five signals: ``STRONG_BUY``, ``BUY``, ``HOLD``,
``SELL`` or ``STRONG_SELL``.  These signals are deliberately kept
simple and interpretable rather than attempting to optimise for any
particular trading strategy.

The algorithm operates as follows:

1. Fetch 300 candlesticks for the requested symbol and interval via the
   Binance service.  Only the closing prices are used for indicator
   computations.
2. Compute the MACD line, its signal line and the histogram using the
   standard (12, 26, 9) periods.
3. Compute the 14‑period RSI using the existing indicators module.
4. Determine the latest values of the MACD line, signal line, histogram
   and RSI.
5. Derive the recommendation based on the relative position of the
   MACD line to its signal and the current RSI:

   * If the MACD line is above the signal line (bullish momentum):
       - ``STRONG_BUY`` if RSI < 30 (oversold market)
       - ``BUY`` if 30 ≤ RSI < 50 (mildly oversold to neutral)
       - ``HOLD`` otherwise
   * If the MACD line is below the signal line (bearish momentum):
       - ``STRONG_SELL`` if RSI > 70 (overbought market)
       - ``SELL`` if 50 < RSI ≤ 70 (neutral to mildly overbought)
       - ``HOLD`` otherwise
   * If either the MACD or signal value is undefined the signal is
     ``HOLD``.

This logic deliberately avoids tuning numeric thresholds too finely.
Traders should interpret the output in the context of their broader
strategy and risk tolerance.
"""

from __future__ import annotations

from typing import List, Optional

from . import binance, indicators, advanced_indicators


def advanced_recommendation(symbol: str, interval: str) -> dict[str, object]:
    """Compute an advanced trading recommendation for a given symbol.

    Parameters
    ----------
    symbol:
        The trading pair symbol (e.g. ``BTCUSDT``).
    interval:
        The candle interval (e.g. ``1h``).

    Returns
    -------
    dict
        A dictionary containing the latest MACD, MACD signal, MACD
        histogram, RSI14 and the derived recommendation.
    """
    # Fetch 300 candlesticks (time, open, high, low, close).  The Binance
    # client returns a list where index 4 is the close price.
    raw = binance.klines(symbol, interval, 300)
    closes: List[float] = [float(r[4]) for r in raw]

    # Compute MACD and RSI values.
    macd_line, signal_line, histogram = advanced_indicators.macd(closes)
    rsi14 = indicators.rsi(closes, 14)

    last = len(closes) - 1
    # Extract the most recent indicator values.  They may be None if
    # insufficient data.
    macd_val: Optional[float] = macd_line[last] if macd_line else None
    signal_val: Optional[float] = signal_line[last] if signal_line else None
    hist_val: Optional[float] = histogram[last] if histogram else None
    rsi_val: Optional[float] = rsi14[last] if rsi14 else None

    # Determine the recommendation.
    sig = "HOLD"
    # Both MACD and signal must be defined to generate a directional signal.
    if macd_val is not None and signal_val is not None:
        if macd_val > signal_val:
            # Bullish momentum
            if rsi_val is not None and rsi_val < 30:
                sig = "STRONG_BUY"
            elif rsi_val is not None and rsi_val < 50:
                sig = "BUY"
            else:
                sig = "HOLD"
        elif macd_val < signal_val:
            # Bearish momentum
            if rsi_val is not None and rsi_val > 70:
                sig = "STRONG_SELL"
            elif rsi_val is not None and rsi_val > 50:
                sig = "SELL"
            else:
                sig = "HOLD"

    return {
        "symbol": symbol,
        "interval": interval,
        "macd": macd_val,
        "macd_signal": signal_val,
        "macd_histogram": hist_val,
        "rsi14": rsi_val,
        "signal": sig,
    }
