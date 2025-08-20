"""Simple price caching layer used by the portfolio service.

To avoid repeatedly fetching ticker prices for the same symbol in quick
succession this module maintains an in‑memory cache keyed by symbol.  A
TTL (time to live) is enforced on each entry to ensure stale prices are
periodically refreshed.  If the underlying ``binance.ticker_price``
raises any exception (e.g. network error) the cache entry is not
updated and ``None`` is returned instead.
"""

from __future__ import annotations

import time
from decimal import Decimal

from . import binance

_CACHE: dict[str, tuple[Decimal, float]] = {}
_TTL = 60.0  # seconds


def get_price_cached(symbol: str) -> Decimal | None:
    """Return the latest price for ``symbol``, consulting a cache.

    If the price is present in the cache and hasn't expired it is
    returned immediately.  Otherwise the price is fetched via
    ``binance.ticker_price``; if successful the cache is refreshed and
    the price is returned.  On error ``None`` is returned and the cache
    remains unchanged.
    """
    now = time.time()
    hit = _CACHE.get(symbol)
    if hit and (now - hit[1] < _TTL):
        return hit[0]
    try:
        price = binance.ticker_price(symbol)
    except Exception:
        return None
    _CACHE[symbol] = (price, now)
    return price
