from fastapi import APIRouter, HTTPException
from decimal import Decimal
from app.services import binance
from app.services.pricing import get_price_cached

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

@router.get("/valued")
def portfolio_valued():
    try:
        acc = binance.account()
    except Exception as e:
        raise HTTPException(400, f"account error: {e}")

    balances = [b for b in acc.get("balances", []) if float(b["free"]) or float(b["locked"])]
    items: list[dict] = []
    total = Decimal("0")

    for b in balances:
        asset = b["asset"]
        free = Decimal(b["free"])
        locked = Decimal(b["locked"])
        qty = free + locked
        if qty == 0:
            continue

        if asset == "USDT":
            price = Decimal("1")
            value = qty * price
            total += value
            items.append({
                "asset": asset, "free": str(free), "locked": str(locked),
                "symbol": "USDTUSDT", "price_usdt": str(price),
                "value_usdt": str(value), "priced": True
            })
            continue

        symbol = f"{asset}USDT"
        price = get_price_cached(symbol)
        if price is not None:
            value = qty * price
            total += value
            items.append({
                "asset": asset, "free": str(free), "locked": str(locked),
                "symbol": symbol, "price_usdt": str(price),
                "value_usdt": str(value), "priced": True
            })
        else:
            items.append({
                "asset": asset, "free": str(free), "locked": str(locked),
                "symbol": symbol, "price_usdt": None,
                "value_usdt": None, "priced": False
            })

    items.sort(key=lambda x: Decimal(x["value_usdt"] or "0"), reverse=True)
    return {"total_usdt": str(total), "items": items}
