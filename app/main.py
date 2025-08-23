"""FastAPI entry point for the crypto trading application.

This module wires up the various API routers defined in the ``app.api``
subpackages and exposes a single FastAPI instance.  It also mounts the
static frontend contained in the ``web`` directory so that navigating
to ``/`` loads the trading interface.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.market import router as market_router  # type: ignore
from app.api.recs import router as recs_router  # type: ignore
from app.api.portfolio import router as portfolio_router  # type: ignore
from app.api.advanced_recs import router as advanced_recs_router  # type: ignore

app = FastAPI(title="Personal Binance Spot Trader", version="1.0.0")

# Register API routers.  The order of inclusion determines the order in
# which routes are matched.  Specific paths should appear before more
# general ones.
app.include_router(market_router)
app.include_router(recs_router)
app.include_router(portfolio_router)
app.include_router(advanced_recs_router)


@app.get("/api/health")
def health() -> dict[str, bool]:
    """Simple health‑check endpoint used to verify that the API is
    responsive.  Returns a JSON object containing a single ``ok`` field.

    This endpoint does not perform any external calls and is therefore
    suitable for use in monitoring or CI environments.
    """
    return {"ok": True}

# Mount static frontend assets.  This exposes the ``web`` directory at the
# root of the API, allowing the HTML/CSS/JS frontend to be served
# without requiring an additional web server.  Compute the absolute
# path to the web directory relative to this file.  Using an absolute
# path ensures that tests run correctly regardless of the current
# working directory.  ``web`` lives one level above this file
# (crypto-trading/app/main.py → crypto-trading/web).
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent.parent / "web"
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="web")

__all__ = ["app"]
