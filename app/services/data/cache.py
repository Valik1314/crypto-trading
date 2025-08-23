"""Caching utilities for market data.

Fetching OHLCV data from remote exchanges can be slow and rate limited.
This module provides a simple caching layer built on top of
:class:`joblib.Memory` to persist the results of expensive calls to
disk.  The default cache location may be overridden by setting the
``DATA_CACHE_DIR`` environment variable.  Caching can be disabled
entirely by setting ``DATA_CACHE_DIR`` to an empty string.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, TypeVar, ParamSpec

from joblib import Memory  # type: ignore

P = ParamSpec("P")
T = TypeVar("T")

_memory: Memory | None = None


def _get_memory() -> Memory:
    """Return a memoising :class:`joblib.Memory` instance.

    The cache directory is created if it doesn't already exist.
    """
    global _memory
    if _memory is not None:
        return _memory
    cache_dir = os.getenv("DATA_CACHE_DIR", "storage/cache/ohlcv").strip()
    if cache_dir == "":
        # Caching disabled
        _memory = Memory(location=None, verbose=0)
        return _memory
    path = Path(cache_dir)
    path.mkdir(parents=True, exist_ok=True)
    _memory = Memory(str(path), verbose=0)
    return _memory


def cached(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator to cache the result of a function using joblib.Memory.

    This decorator wraps the provided function and stores its results in
    the cache directory.  Use it for IO‑bound functions such as OHLCV
    retrieval where repeated calls with the same arguments should return
    quickly.
    """

    memory = _get_memory()
    cached_func = memory.cache(func)

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        return cached_func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
