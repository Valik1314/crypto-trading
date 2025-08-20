import time
from decimal import Decimal
from . import binance

_CACHE: dict[str, tuple[Decimal, float]] = {}
_TTL = 60.0  # секунд

def get_price_cached(symbol: str) -> Decimal | None:
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
