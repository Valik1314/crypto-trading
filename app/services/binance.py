import os, hmac, hashlib, time
from decimal import Decimal
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY     = os.getenv("BINANCE_API_KEY", "")
API_SECRET  = os.getenv("BINANCE_API_SECRET", "")
USE_TESTNET = os.getenv("USE_TESTNET", "0") == "1"

BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com").rstrip("/")
if USE_TESTNET:
    # тестовая среда (для торговли); публичные цены тоже есть
    BASE_URL = "https://testnet.binance.vision"

session = requests.Session()
if API_KEY:
    session.headers.update({"X-MBX-APIKEY": API_KEY})

def _sign(params: dict) -> dict:
    if not API_SECRET:
        raise RuntimeError("BINANCE_API_SECRET не задан (.env)")
    # важен исходный порядок ключей
    qs = "&".join(f"{k}={params[k]}" for k in params)
    sig = hmac.new(API_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    params["signature"] = sig
    return params

def _get(path: str, params: dict | None = None, auth: bool = False):
    url = f"{BASE_URL}{path}"
    p = dict(params or {})
    if auth:
        p.update({"timestamp": int(time.time() * 1000), "recvWindow": 5000})
        p = _sign(p)
    r = session.get(url, params=p, timeout=20)
    r.raise_for_status()
    return r.json()

# --- публичные ---
def klines(symbol: str, interval: str, limit: int = 300) -> list[list]:
    return _get("/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})

def ticker_price(symbol: str) -> Decimal:
    data = _get("/api/v3/ticker/price", {"symbol": symbol})
    return Decimal(data["price"])

# --- приватные ---
def account() -> dict:
    if not API_KEY or not API_SECRET:
        raise RuntimeError("API ключи не заданы (.env)")
    return _get("/api/v3/account", auth=True)
