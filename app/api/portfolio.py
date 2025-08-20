"""Portfolio valuation API.

This module exposes an endpoint that returns the current account balances
along with a best‑effort valuation in USDT.  It relies on the account
information provided by the Binance API and uses a simple caching layer
defined in ``app.services.pricing`` to avoid repeated ticker lookups.
"""

from decimal import Decimal
from fastapi import APIRouter, HTTPException

from app.services import binance
from app.services.pricing import get_price_cached


router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/valued")
def portfolio_valued() -> dict[str, object]:
    """Return balances and their approximate value in USDT.

    The underlying Binance ``account`` call requires API keys; if none
    are configured an HTTP 400 is returned with a descriptive error.  For
    each asset with non‑zero quantity the endpoint attempts to fetch the
    current price and compute the total value.  Assets with unknown
    prices are still returned but marked ``unpriced`` in the result.  A
    sorted list of items along with the total USDT value is returned.
    """
    try:
        acc = binance.account()
    except Exception as exc:
        raise HTTPException(400, f"account error: {exc}") from exc

    balances = [
        b
        for b in acc.get("balances", [])
        if float(b.get("free", 0)) or float(b.get("locked", 0))
    ]
    items: list[dict[str, object]] = []
    total = Decimal("0")
    for b in balances:
        asset = b["asset"]
        free = Decimal(b["free"])
        locked = Decimal(b["locked"])
        qty = free + locked
        if qty == 0:
            continue
        # Stablecoin: trivially valued at 1 USDT per unit
        if asset == "USDT":
            price = Decimal("1")
            value = qty * price
            total += value
            items.append(
                {
                    "asset": asset,
                    "free": str(free),
                    "locked": str(locked),
                    "symbol": "USDTUSDT",
                    "price_usdt": str(price),
                    "value_usdt": str(value),
                    "priced": True,
                }
            )
            continue
        symbol = f"{asset}USDT"
        price = get_price_cached(symbol)
        if price is not None:
            value = qty * price
            total += value
            items.append(
                {
                    "asset": asset,
                    "free": str(free),
                    "locked": str(locked),
                    "symbol": symbol,
                    "price_usdt": str(price),
                    "value_usdt": str(value),
                    "priced": True,
                }
            )
        else:
            items.append(
                {
                    "asset": asset,
                    "free": str(free),
                    "locked": str(locked),
                    "symbol": symbol,
                    "price_usdt": None,
                    "value_usdt": None,
                    "priced": False,
                }
            )
    # Sort by value descending; unpriced values are treated as zero
    items.sort(key=lambda x: Decimal(x["value_usdt"] or "0"), reverse=True)
    return {"total_usdt": str(total), "items": items}
