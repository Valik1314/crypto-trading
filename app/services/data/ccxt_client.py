"""Thin wrapper around the ccxt library for fetching OHLCV data.

The purpose of this module is to encapsulate exchange initialisation and
provide a simple function for retrieving historical candles.  By
isolating `ccxt` usage in its own module the rest of the codebase
remains decoupled from the specifics of any one exchange.  Should the
application ever need to support multiple exchanges or mock the data
layer for testing, this module can be swapped out with minimal
changes elsewhere.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Dict, Any

import pandas as pd  # type: ignore

try:
    import ccxt  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "ccxt must be installed to use the data services (see requirements.txt)"
    ) from exc


@lru_cache(maxsize=1)
def _get_exchange(name: str = "binance") -> "ccxt.Exchange":
    """Return a cached ccxt exchange instance.

    The exchange is created with sane defaults (rate limiting enabled and
    time difference adjustments).  The cache ensures that the same
    instance is reused across calls to avoid unnecessary reconnections.

    Parameters
    ----------
    name:
        The exchange identifier supported by ccxt (defaults to ``binance``).

    Returns
    -------
    ccxt.Exchange
        A configured ccxt exchange instance.
    """
    cls = getattr(ccxt, name)
    return cls({
        "enableRateLimit": True,
        # Adjust for potential time drift between client and exchange
        "options": {"adjustForTimeDifference": True},
    })



def fetch_ohlcv(
    symbol: str,
    timeframe: str,
    *,
    limit: int = 500,
    exchange: str = "binance",
) -> pd.DataFrame:
    """Fetch OHLCV data for a symbol and timeframe.

    Parameters
    ----------
    symbol:
        The trading pair in ``BASE/QUOTE`` format (e.g. ``BTC/USDT``).
    timeframe:
        The ccxt timeframe code (e.g. ``1m``, ``5m``, ``1h``, ``1d``).
    limit:
        The maximum number of candles to retrieve.  Note that some
        exchanges cap the maximum at 1000.
    exchange:
        Optional name of the ccxt exchange (defaults to ``binance``).

    Returns
    -------
    pandas.DataFrame
        A dataframe with columns ``timestamp`` (UTC datetime), ``open``,
        ``high``, ``low``, ``close`` and ``volume``.  The ``timestamp``
        column is converted from milliseconds to pandas ``datetime64[ns]``.
    """
    ex = _get_exchange(exchange)
    data: List[List[Any]] = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(
        data,
        columns=["timestamp", "open", "high", "low", "close", "volume"],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df
