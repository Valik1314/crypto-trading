"""Thin client for Binance REST API used by the application.

The functions defined in this module wrap the public and private REST
endpoints exposed by Binance.  API keys are loaded from environment
variables (via the optional ``python‑dotenv`` package) and used when
available.  When keys are missing, private methods will raise an
exception instead of silently failing.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from decimal import Decimal

import requests

# ``dotenv`` is an optional dependency.  When it isn't installed we
# provide a no‑op fallback to avoid ImportError on import.
try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover
    def load_dotenv(*_args: object, **_kwargs: object) -> None:
        return None

# Load variables from a ``.env`` file if present.  Missing dotenv is
# silently ignored by the fallback above.
load_dotenv()

# API keys/secrets and base URL configuration.  A blank key/secret
# indicates that private endpoints are unavailable.
API_KEY: str = os.getenv("BINANCE_API_KEY", "")
API_SECRET: str = os.getenv("BINANCE_API_SECRET", "")
USE_TESTNET: bool = os.getenv("USE_TESTNET", "0") == "1"

BASE_URL: str = os.getenv("BINANCE_BASE_URL", "https://api.binance.com").rstrip("/")
if USE_TESTNET:
    # Use testnet base URL when enabled; note that public data endpoints are
    # also available on the testnet domain.
    BASE_URL = "https://testnet.binance.vision"

# Preconfigure a session to reuse connections.  When an API key is
# provided we automatically add the X‑MBX‑APIKEY header expected by
# Binance.
session = requests.Session()
if API_KEY:
    session.headers.update({"X-MBX-APIKEY": API_KEY})


def _sign(params: dict[str, object]) -> dict[str, object]:
    """Attach an HMAC‑SHA256 signature to a dictionary of params.

    Binance requires that query parameters are signed using your API
    secret for private endpoints.  The signature is computed over the
    raw querystring with keys in their original order.
    """
    if not API_SECRET:
        raise RuntimeError("BINANCE_API_SECRET не задан (.env)")
    qs = "&".join(f"{k}={params[k]}" for k in params)
    signature = hmac.new(API_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    params["signature"] = signature
    return params


def _get(path: str, params: dict[str, object] | None = None, auth: bool = False) -> dict:
    """Issue a GET request to the given Binance API path.

    Parameters
    ----------
    path:
        The path fragment (e.g. ``"/api/v3/klines"``) to append to the
        configured base URL.
    params:
        A dictionary of query parameters; may be ``None``.
    auth:
        When ``True`` adds a timestamp and signature to the query
        parameters.  This is required for private endpoints.

    Returns
    -------
    dict
        The JSON payload returned by Binance.  Any HTTP error will
        result in :class:`requests.HTTPError` being raised.
    """
    url = f"{BASE_URL}{path}"
    query = dict(params or {})
    if auth:
        query.update({"timestamp": int(time.time() * 1000), "recvWindow": 5000})
        query = _sign(query)  # type: ignore[assignment]
    resp = session.get(url, params=query, timeout=20)
    resp.raise_for_status()
    return resp.json()


# --- public endpoints ---

def klines(symbol: str, interval: str, limit: int = 300) -> list[list]:
    """Return historical klines (candlesticks) for a given symbol and interval."""
    return _get("/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})  # type: ignore[return-value]



def ticker_price(symbol: str) -> Decimal:
    """Return the latest price for the given symbol as a Decimal."""
    data: dict[str, str] = _get("/api/v3/ticker/price", {"symbol": symbol})  # type: ignore[assignment]
    return Decimal(data["price"])


# --- private endpoints ---

def account() -> dict:
    """Return account information for the authenticated user.

    Raises a :class:`RuntimeError` if API keys are not configured.  The
    underlying request may raise an HTTPError if Binance returns an
    error.
    """
    if not API_KEY or not API_SECRET:
        raise RuntimeError("API ключи не заданы (.env)")
    return _get("/api/v3/account", auth=True)
