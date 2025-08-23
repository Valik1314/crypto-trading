"""Additional technical indicators used by the advanced recommendation engine.

The basic project implements only EMA and RSI.  To support more nuanced
signals this module adds computations for the Moving Average Convergence
Divergence (MACD) oscillator.  The implementation builds on the
existing EMA function from ``app.services.indicators``.
"""

from typing import Iterable, List, Optional, Tuple

from . import indicators


def macd(
    closes: Iterable[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """Compute the MACD line, signal line and histogram for a series of closes.

    Parameters
    ----------
    closes:
        An iterable of closing prices.
    fast:
        The number of periods for the fast EMA.  Defaults to 12.
    slow:
        The number of periods for the slow EMA.  Defaults to 26.
    signal:
        The number of periods for the signal line EMA.  Defaults to 9.

    Returns
    -------
    tuple
        A tuple of three lists: (macd_line, signal_line, histogram).
        ``None`` values denote positions where the indicator is not yet
        defined due to insufficient data.
    """
    closes = list(closes)
    if not closes:
        return [], [], []

    # Compute the fast and slow EMA series using the existing implementation.
    ema_fast = indicators.ema(closes, fast)
    ema_slow = indicators.ema(closes, slow)

    # Calculate the MACD line as the difference between fast and slow EMAs.
    macd_line: List[Optional[float]] = []
    for f, s in zip(ema_fast, ema_slow):
        if f is None or s is None:
            macd_line.append(None)
        else:
            macd_line.append(f - s)

    # To compute the signal line we need a numeric series.  Replace None
    # values with 0.0; these placeholder values occur only during the
    # initial periods where the MACD is undefined and will be ignored by
    # the EMA algorithm.
    numeric_macd = [m if m is not None else 0.0 for m in macd_line]
    signal_line: List[Optional[float]] = indicators.ema(numeric_macd, signal)

    # Histogram is MACD line minus its signal line when both values are
    # defined.  For undefined positions the histogram is ``None``.
    histogram: List[Optional[float]] = []
    for m, s_val in zip(macd_line, signal_line):
        if m is None or s_val is None:
            histogram.append(None)
        else:
            histogram.append(m - s_val)

    return macd_line, signal_line, histogram
