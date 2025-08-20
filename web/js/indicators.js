window.App = window.App || {};
App.indicators = {
  calcEMA(data, period) {
    const k = 2 / (period + 1);
    const out = [];
    let ema = null;
    data.forEach((c, i) => {
      if (i < period - 1) { out.push(null); return; }
      if (ema === null) ema = data.slice(0, period).reduce((s, x) => s + x.close, 0) / period;
      else ema = (c.close - ema) * k + ema;
      out.push(ema);
    });
    return out;
  },
  calcRSI(data, period = 14) {
    const out = []; let gains = 0, losses = 0;
    for (let i = 1; i < data.length; i++) {
      const d = data[i].close - data[i-1].close;
      if (i <= period) { if (d >= 0) gains += d; else losses -= d; out.push(null); }
      else {
        gains = (gains * (period - 1) + Math.max(d, 0)) / period;
        losses = (losses * (period - 1) + Math.max(-d, 0)) / period;
        const rs = gains / Math.max(losses, 1e-9);
        out.push(100 - 100 / (1 + rs));
      }
    }
    return out;
  }
};
