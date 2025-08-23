"""Service layer for the crypto trading application.

Modules in this package implement low‑level integrations (such as
Binance REST calls) and indicator computations.  The service layer is
designed to be stateless and free of FastAPI dependencies so that it
can be imported from both API handlers and unit tests.
"""

# Re-export commonly used services so callers can import from
# ``app.services`` rather than deeper package paths.  This mirrors the
# existing structure in the original repository.

from . import binance  # noqa: F401
from . import indicators  # noqa: F401
from . import advanced_indicators  # noqa: F401
from . import advanced_recommender  # noqa: F401

__all__ = [
    "binance",
    "indicators",
    "advanced_indicators",
    "advanced_recommender",
]
