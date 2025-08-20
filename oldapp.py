import os, hmac, hashlib, time
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP, getcontext
from typing import Dict, Any, List, Optional

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Высокая точность для финансовых расчётов
getcontext().prec = 28

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")
BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com").rstrip("/")
DATA_BASE_URL = os.getenv("BINANCE_DATA_BASE_URL", "https://data-api.binance.vision").rstrip("/")
USE_TESTNET = os.getenv("USE_TESTNET", "1") == "1"
if USE_TESTNET:
    BASE_URL = "https://testnet.binance.vision"

session = requests.Session()
if API_KEY:
    session.headers.update({"X-MBX-APIKEY": API_KEY})

app = FastAPI(title="Personal Binance Spot Trader", version="1.0.0")

# ---------- Утилиты ----------

def _sign(params: Dict[str, Any]) -> Dict[str, Any]:
    """Подпись HMAC SHA256 по оригинальному порядку параметров."""
    if not API_SECRET:
        raise HTTPException(400, "API ключи не заданы (.env)")
    qs = "&".join(f"{k}={params[k]}" for k in params)  # без сортировки
    sig = hmac.new(API_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    params["signature"] = sig
    return params

def _get(url: str, params: Dict[str, Any] = None, auth: bool = False) -> Any:
    p = dict(params or {})
    if auth:
        p.update({"timestamp": int(time.time() * 1000), "recvWindow": 5000})
        p = _sign(p)
    r = session.get(url, params=p, timeout=20)
    if not r.ok:
        raise HTTPException(r.status_code, r.text)
    return r.json()

def _post(url: str, params: Dict[str, Any] = None, auth: bool = True) -> Any:
    p = dict(params or {})
    if auth:
        p.update({"timestamp": int(time.time() * 1000), "recvWindow": 5000})
        p = _sign(p)
    r = session.post(url, params=p, timeout=20)
    if not r.ok:
        raise HTTPException(r.status_code, r.text)
    return r.json()

def _dec(x) -> Decimal:
    return Decimal(str(x))

def quantize_step(value: Decimal, step: Decimal) -> Decimal:
    """Округление вниз к сетке шага (LOT_SIZE)."""
    return (value // step) * step

def quantize_tick(value: Decimal, tick: Decimal) -> Decimal:
    """Округление до тика цены (PRICE_FILTER)."""
    return value.quantize(tick, rounding=ROUND_HALF_UP)

def ema(closes: List[float], period: int) -> List[Optional[float]]:
    if period <= 1 or not closes:
        return [None] * len(closes)
    res: List[Optional[float]] = [None] * len(closes)
    alpha = 2.0 / (period + 1.0)
    # первичный SMA
    if len(closes) < period:
        return res
    avg = sum(closes[:period]) / period
    res[period - 1] = avg
    for i in range(period, len(closes)):
        avg = closes[i] * alpha + avg * (1 - alpha)
        res[i] = avg
    return res

def rsi(closes: List[float], period: int = 14) -> List[Optional[float]]:
    n = len(closes)
    out: List[Optional[float]] = [None] * n
    if n <= period:
        return out
    gains, losses = 0.0, 0.0
    for i in range(1, period + 1):
        ch = closes[i] - closes[i - 1]
        if ch >= 0: gains += ch
        else:       losses -= ch
    avg_g, avg_l = gains / period, losses / period
    for i in range(period, n):
        if i > period:
            ch = closes[i] - closes[i - 1]
            g = max(ch, 0.0)
            l = max(-ch, 0.0)
            avg_g = (avg_g * (period - 1) + g) / period
            avg_l = (avg_l * (period - 1) + l) / period
        rs = float('inf') if avg_l == 0 else avg_g / avg_l
        out[i] = 100 - 100 / (1 + rs)
    return out

# ---------- Схемы ----------

class PreviewReq(BaseModel):
    symbol: str               # BTCUSDT
    side: str                 # BUY / SELL
    quote_amount: float       # сумма в котируемой валюте (USDT)
    sl_pct: float             # стоп-лосс (доля, напр. 0.01)
    tp_r_multiple: float      # тейк = sl_pct * R (напр. 2.0)

# ---------- API (префикс /api/*) ----------

@app.get("/api/health", include_in_schema=False)
def health():
    return {"ok": True, "use_testnet": USE_TESTNET}

@app.get("/api/klines")
def api_klines(symbol: str = Query(..., pattern=r"^[A-Z0-9]+$"),
               interval: str = Query("1h"),
               limit: int = Query(300, ge=50, le=1000)):
    """
    Исторические свечи + индикаторы EMA12/EMA26/RSI14 для фронта.
    Публичный data endpoint → ключи не требуются.
    """
    url = f"{DATA_BASE_URL}/api/v3/klines"
    data = _get(url, {"symbol": symbol, "interval": interval, "limit": limit})
    closes = [float(x[4]) for x in data]
    times = [x[0] for x in data]
    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    rsi14 = rsi(closes, 14)

    kl = [{"t": t,
           "o": float(d[1]), "h": float(d[2]), "l": float(d[3]), "c": float(d[4])}
          for t, d in zip(times, data)]
    return {"klines": kl, "ema12": ema12, "ema26": ema26, "rsi14": rsi14}

@app.get("/api/recommendations")
def api_recommendations(symbol: str, interval: str = "1h"):
    """
    Простейший сигнал: кросс EMA12/EMA26 + фильтр RSI.
    """
    payload = api_klines(symbol=symbol, interval=interval, limit=300)
    ema12, ema26, rsi14 = payload["ema12"], payload["ema26"], payload["rsi14"]
    last = len(payload["klines"]) - 1
    # находим последний валидный индекс
    while last > 0 and (ema12[last] is None or ema26[last] is None or rsi14[last] is None):
        last -= 1
    if last <= 0:
        return {"symbol": symbol, "interval": interval, "signal": "HOLD", "reason": "not_enough_data"}
    prev = last - 1
    cross_up = ema12[prev] <= ema26[prev] and ema12[last] > ema26[last]
    cross_dn = ema12[prev] >= ema26[prev] and ema12[last] < ema26[last]
    r = rsi14[last]
    signal, reason = "HOLD", "no_cross"
    if cross_up and 45 <= r <= 65: signal, reason = "BUY",  f"ema12>ema26 & rsi={round(r,1)}"
    if cross_dn and 35 <= r <= 60: signal, reason = "SELL", f"ema12<ema26 & rsi={round(r,1)}"
    return {"symbol": symbol, "interval": interval, "signal": signal, "reason": reason,
            "ema12": ema12[last], "ema26": ema26[last], "rsi14": r}

@app.post("/api/orders/preview")
def api_orders_preview(req: PreviewReq):
    """
    Предрасчёт сделки:
    - exchangeInfo → шаги лота/цены, minNotional
    - текущая цена → /ticker/price
    - qty из quote_amount/price, округление по stepSize
    - расчёт SL/TP с округлением по tickSize
    """
    sym = req.symbol.upper()

    # exchangeInfo (ищем нужный символ)
    info = _get(f"{BASE_URL}/api/v3/exchangeInfo")
    sym_info = next((s for s in info["symbols"] if s["symbol"] == sym), None)
    if not sym_info:
        raise HTTPException(400, f"symbol {sym} not found")

    def f(name): return next((x for x in sym_info["filters"] if x["filterType"] == name), None)
    lot = f("LOT_SIZE"); pricef = f("PRICE_FILTER"); minnot = f("MIN_NOTIONAL")

    step = _dec(lot["stepSize"])
    tick = _dec(pricef["tickSize"])
    min_notional = _dec(minnot["minNotional"]) if minnot and minnot.get("minNotional") else None

    # текущая цена
    p = _get(f"{BASE_URL}/api/v3/ticker/price", {"symbol": sym})
    price = _dec(p["price"])

    # размер позиции из суммы в котируемой валюте
    raw_qty = _dec(req.quote_amount) / price
    qty = quantize_step(raw_qty, step)
    if qty <= 0:
        raise HTTPException(400, f"quote_amount слишком мал для шага лота (step={step})")

    # SL/TP
    sl_factor = _dec(req.sl_pct)
    tp_mult = _dec(req.tp_r_multiple)
    if req.side.upper() == "BUY":
        sl_price = quantize_tick(price * (Decimal(1) - sl_factor), tick)
        tp_price = quantize_tick(price * (Decimal(1) + sl_factor * tp_mult), tick)
    else:
        sl_price = quantize_tick(price * (Decimal(1) + sl_factor), tick)
        tp_price = quantize_tick(price * (Decimal(1) - sl_factor * tp_mult), tick)

    notional = price * qty
    if min_notional and notional < min_notional:
        raise HTTPException(400, f"notional {notional} < minNotional {min_notional}")

    return {
        "symbol": sym, "side": req.side.upper(),
        "price": str(price), "qty": str(qty.normalize()),
        "sl_price": str(sl_price), "tp_price": str(tp_price),
        "step_size": str(step), "tick_size": str(tick),
        "min_notional": str(min_notional) if min_notional else None
    }

@app.post("/api/orders/confirm")
def api_orders_confirm(payload: Dict[str, Any]):
    """
    BUY/SELL MARKET + OCO (TP/SL) для спота.
    REQUIREMENTS: API_KEY/SECRET в .env. На тестнете OCO может быть ограничен — тогда fallback.
    """
    if not API_KEY or not API_SECRET:
        raise HTTPException(400, "API ключи не заданы (.env)")

    symbol = payload["symbol"].upper()
    side = payload["side"].upper()
    qty = payload["qty"]
    sl = payload["sl_price"]
    tp = payload["tp_price"]

    # 1) MARKET
    order = _post(f"{BASE_URL}/api/v3/order", {
        "symbol": symbol, "side": side, "type": "MARKET", "quantity": qty
    }, auth=True)

    # 2) OCO (для BUY → SELL). Если не поддерживается — fallback на отдельные ордера.
    oco = None
    if side == "BUY":
        try:
            oco = _post(f"{BASE_URL}/api/v3/order/oco", {
                "symbol": symbol, "side": "SELL", "quantity": qty,
                "price": tp, "stopPrice": sl, "stopLimitPrice": sl, "stopLimitTimeInForce": "GTC"
            }, auth=True)
        except HTTPException:
            # Fallback: отдельно LIMIT TP и STOP_LOSS_LIMIT
            _post(f"{BASE_URL}/api/v3/order", {
                "symbol": symbol, "side": "SELL", "type": "LIMIT", "timeInForce": "GTC",
                "quantity": qty, "price": tp
            }, auth=True)
            _post(f"{BASE_URL}/api/v3/order", {
                "symbol": symbol, "side": "SELL", "type": "STOP_LOSS_LIMIT", "timeInForce": "GTC",
                "quantity": qty, "price": sl, "stopPrice": sl
            }, auth=True)

    return JSONResponse({
        "status": order.get("status", "ACK"),
        "orderId": order.get("orderId"),
        "tp_orderListId": oco.get("orderListId") if oco else None
    })

@app.get("/api/portfolio")
def api_portfolio():
    """Свободные балансы аккаунта (скрываем нули). Требует ключи."""
    if not API_KEY or not API_SECRET:
        raise HTTPException(400, "API ключи не заданы (.env)")
    acc = _get(f"{BASE_URL}/api/v3/account", auth=True)
    bals = [b for b in acc["balances"] if float(b["free"]) or float(b["locked"])]
    return {"balances": bals}

# ---------- Статика в корне (последним, чтобы не перекрыть /api/*) ----------
app.mount("/", StaticFiles(directory="web", html=True), name="web")
