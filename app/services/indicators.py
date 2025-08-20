"""Technical indicator computations.

This module implements a handful of commonly used indicators without any
external dependencies.  The functions operate on iterables of floats and
return lists of indicator values, using ``None`` to represent periods
before the indicator becomes valid.
"""

from typing import Iterable, List, Optional


def ema(closes: Iterable[float], period: int) -> List[Optional[float]]:
    """Compute the exponential moving average of a series of closes.

    Parameters
    ----------
    closes:
        An iterable of closing prices.
    period:
        The number of periods to use for the average.  If ``period`` is
        less than or equal to one or ``closes`` is empty a list of
        ``None`` values of the same length as ``closes`` is returned.

    Returns
    -------
    list
        A list where values before ``period-1`` are ``None`` and
        subsequent values are the exponentially smoothed moving average.
    """
    closes = list(closes)
    out: List[Optional[float]] = []
    if period <= 1 or len(closes) == 0:
        return [None] * len(closes)
    k = 2 / (period + 1)
    ema_val: Optional[float] = None
    for i, c in enumerate(closes):
        if i < period - 1:
            out.append(None)
            continue
        if ema_val is None:
            ema_val = sum(closes[:period]) / period
        else:
            ema_val = (c - ema_val) * k + ema_val
        out.append(ema_val)
    return out


def rsi(closes: Iterable[float], period: int = 14) -> List[Optional[float]]:
    """Compute the Relative Strength Index (RSI) of a series of closes.

    Parameters
    ----------
    closes:
        An iterable of closing prices.
    period:
        The lookback window for the RSI.  Defaults to 14.

    Returns
    -------
    list
        A list where the first element is ``None`` and elements up to
        ``period`` are ``None``.  Subsequent elements contain the RSI
        values in the range 0‑100.
    """
    closes = list(closes)
    out: List[Optional[float]] = [None]
    gains = 0.0
    losses = 0.0
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        if i <= period:
            if diff >= 0:
                gains += diff
            else:
                losses -= diff
            out.append(None)
        else:
            gains = (gains * (period - 1) + max(diff, 0)) / period
            losses = (losses * (period - 1) + max(-diff, 0)) / period
            rs = gains / (losses or 1e-9)
            out.append(100 - 100 / (1 + rs))
    return out
