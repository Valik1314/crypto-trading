from typing import Iterable, List, Optional

def ema(closes: Iterable[float], period: int) -> List[Optional[float]]:
    closes = list(closes)
    out: List[Optional[float]] = []
    if period <= 1 or len(closes) == 0:
        return [None]*len(closes)
    k = 2 / (period + 1)
    ema_val = None
    for i, c in enumerate(closes):
        if i < period - 1:
            out.append(None)
            continue
        if ema_val is None:
            ema_val = sum(closes[:period]) / period
        else:
            ema_val = (c - ema_val) * k + ema_val
        out.append(ema_val)
    return out

def rsi(closes: Iterable[float], period: int = 14):
    closes = list(closes)
    out = [None]
    gains = 0.0
    losses = 0.0
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if i <= period:
            if diff >= 0: gains += diff
            else: losses -= diff
            out.append(None)
        else:
            gains = (gains * (period - 1) + max(diff, 0)) / period
            losses = (losses * (period - 1) + max(-diff, 0)) / period
            rs = gains / (losses or 1e-9)
            out.append(100 - 100 / (1 + rs))
    return out
