"""Functions for filling missing candles in OHLCV time series.

Cryptocurrency exchanges occasionally return incomplete candlestick data
with missing intervals.  To ensure downstream calculations operate on a
continuous time series this module provides helpers to insert missing
candles and fill their values appropriately.  The simplest strategy is
to forward fill OHLC values using the previous candle's close and set
volume to zero; more sophisticated approaches (e.g. interpolation) can
be implemented as needed.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd  # type: ignore

from .resampler import TIMEFRAME_MAPPING


def fill_gaps(df: pd.DataFrame, method: str = "ffill", timeframe: str | None = None) -> pd.DataFrame:
    """Fill missing values or candles in a DataFrame.

    Two different use cases are supported:

    * **General time series** – When ``timeframe`` is ``None`` the
      ``df`` is assumed to be an arbitrary pandas DataFrame with a
      monotonic index and one or more columns.  Missing values (``NaN``)
      are filled according to ``method``:

      - ``"ffill"``: forward fill missing values.
      - ``"linear"``: linear interpolation between known values.
      - ``"zero"``: replace missing values with zero.

      The index of the input DataFrame is preserved and no new rows
      are added or removed.

    * **OHLCV candlestick series** – When ``timeframe`` is provided the
      DataFrame is expected to contain columns ``timestamp``, ``open``,
      ``high``, ``low``, ``close`` and ``volume``.  The function will
      ensure that there are no missing candles by inserting rows at
      regular intervals defined by ``timeframe`` (see
      :data:`TIMEFRAME_MAPPING`).  The OHLC fields of missing candles
      are forward filled from the previous close and volume is set to
      zero.

    Parameters
    ----------
    df:
        The input DataFrame to fill.
    method:
        The fill method for general time series (ignored when
        ``timeframe`` is provided).  Must be one of ``"ffill"``,
        ``"linear"`` or ``"zero"``.  Defaults to ``"ffill"``.
    timeframe:
        Optional candle interval (e.g. ``"1h"``, ``"1d"``).  When
        provided the OHLCV filling behaviour is used.  Must be present
        in :data:`TIMEFRAME_MAPPING`.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with missing values or candles filled according to
        the specified parameters.
    """
    import numpy as np  # local import to avoid global dependency if unused

    # If timeframe is not provided, operate on a generic DataFrame using the
    # requested fill method.  No rows are added or removed.
    if timeframe is None:
        if method not in {"ffill", "linear", "zero"}:
            raise ValueError(f"Unsupported fill method: {method}")
        # Copy to avoid mutating original
        out = df.copy()
        if method == "ffill":
            out = out.ffill()
        elif method == "linear":
            out = out.interpolate(method="linear")
        elif method == "zero":
            out = out.fillna(0)
        return out

    # timeframe specified: assume OHLCV dataset with timestamp column
    if timeframe not in TIMEFRAME_MAPPING:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    rule = TIMEFRAME_MAPPING[timeframe]
    # Set index and ensure sorted
    if "timestamp" not in df.columns:
        raise ValueError("OHLCV DataFrame must contain a 'timestamp' column when timeframe is provided")
    working = df.set_index("timestamp").sort_index()
    if working.empty:
        return working.reset_index()
    start = working.index.min()
    end = working.index.max()
    full_index = pd.date_range(start=start, end=end, freq=rule)
    # Reindex to full index, preserving existing values
    reindexed = working.reindex(full_index)
    # Forward fill OHLC values; volume missing values become zero
    # For the first missing values we cannot forward fill, so use the
    # first available close for all OHLC fields
    first_valid_close: Optional[float] = None
    if not working["close"].empty:
        first_valid_close = float(working["close"].iloc[0])
    # forward fill existing values
    reindexed[["open", "high", "low", "close"]] = reindexed[["open", "high", "low", "close"]].ffill()
    # fill initial NaNs with the first valid close
    if first_valid_close is not None:
        reindexed[["open", "high", "low", "close"]] = reindexed[["open", "high", "low", "close"]].fillna(first_valid_close)
    # volume: fill missing with 0
    reindexed["volume"] = reindexed["volume"].fillna(0)
    reindexed.reset_index(inplace=True)
    reindexed.rename(columns={"index": "timestamp"}, inplace=True)
    return reindexed
