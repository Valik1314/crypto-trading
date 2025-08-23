"""Timeframe resampling utilities.

Different exchanges and libraries may support a variety of candle
timeframes.  This module defines a mapping from human‑friendly
intervals to pandas resample rules and provides helper functions for
resampling OHLCV dataframes into a desired timeframe.  Resampling is
useful when normalising data from multiple sources or when filling
missing candles.
"""

from __future__ import annotations

import pandas as pd  # type: ignore
from typing import Dict

# Mapping of timeframe strings to pandas offset aliases.  This mapping
# covers the common intervals used in cryptocurrency trading.
TIMEFRAME_MAPPING: Dict[str, str] = {
    "1m": "1T",
    "3m": "3T",
    "5m": "5T",
    "15m": "15T",
    "30m": "30T",
    "1h": "1H",
    "2h": "2H",
    "4h": "4H",
    "6h": "6H",
    "8h": "8H",
    "12h": "12H",
    "1d": "1D",
    "3d": "3D",
    "1w": "1W",
    "1M": "1M",
}


def resample_ohlcv(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample an OHLCV DataFrame to the specified timeframe.

    Parameters
    ----------
    df:
        A DataFrame with a ``timestamp`` datetime index and columns
        ``open``, ``high``, ``low``, ``close`` and ``volume``.
    timeframe:
        The desired timeframe (e.g. ``1h``, ``4h``).  Must be present in
        :data:`TIMEFRAME_MAPPING`.

    Returns
    -------
    pandas.DataFrame
        A new DataFrame resampled to the specified interval.  The
        ``timestamp`` index is reset to a column after resampling.
    """
    if timeframe not in TIMEFRAME_MAPPING:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    rule = TIMEFRAME_MAPPING[timeframe]
    # Ensure the timestamp is the index and sorted
    ts = df.set_index("timestamp").sort_index()
    ohlc_dict = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    resampled = ts.resample(rule).apply(ohlc_dict)
    resampled = resampled.dropna(how="all")
    resampled.reset_index(inplace=True)
    return resampled


class Resampler:
    """Utility class providing a static resample method.

    This class exists for backwards compatibility with existing tests and
    example code which expect a ``Resampler`` type with a ``resample``
    method.  It delegates to :func:`pandas.DataFrame.resample` using a
    sensible aggregation for OHLCV data.  If the input DataFrame has
    columns named ``open``, ``high``, ``low``, ``close`` and ``volume``
    these are aggregated in the standard way; otherwise numeric
    columns are summed by default.
    """

    @staticmethod
    def resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
        """Resample a DataFrame by the given pandas offset rule.

        Parameters
        ----------
        df:
            A DataFrame indexed by a datetime‑like index.
        rule:
            A pandas offset alias (e.g. ``"5T"``, ``"1H"``) describing
            the resample interval.

        Returns
        -------
        pandas.DataFrame
            A resampled DataFrame aggregated by the appropriate
            functions for OHLCV data or using sum for other columns.
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise TypeError("DataFrame must have a DatetimeIndex for resampling")
        # Determine aggregation mapping
        if {"open", "high", "low", "close", "volume"}.issubset(df.columns):
            agg = {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        else:
            # For any other numeric columns use sum
            agg = {col: "sum" for col in df.columns if pd.api.types.is_numeric_dtype(df[col])}
        resampled = df.resample(rule).agg(agg)
        # Drop rows with all NaN values resulting from upsample
        resampled = resampled.dropna(how="all")
        return resampled
