(function () {
  const $ = App.$; const api = App.api;

  document.addEventListener('DOMContentLoaded', () => {
    const chartEl = $('chart'), rsiEl = $('rsiChart');
    const chartApi = LightweightCharts.createChart(chartEl, {
      width: chartEl.clientWidth || 900, height: 520,
      layout: { background:{ type:'solid', color:'#0f1115' }, textColor:'#d7d8db' },
      grid: { vertLines:{ color:'#202432' }, horzLines:{ color:'#202432' } },
      rightPriceScale: { borderVisible:false }, timeScale: { borderVisible:false },
      crosshair: { mode: LightweightCharts.CrosshairMode.Normal }
    });
    const rsiApi = LightweightCharts.createChart(rsiEl, {
      width: rsiEl.clientWidth || 900, height: 160,
      layout: { background:{ type:'solid', color:'#0f1115' }, textColor:'#d7d8db' },
      grid: { vertLines:{ color:'#202432' }, horzLines:{ color:'#202432' } },
      rightPriceScale: { borderVisible:false }, timeScale: { borderVisible:false }
    });

    const candleSeries = chartApi.addCandlestickSeries();
    const ema12Series  = chartApi.addLineSeries({ lineWidth:2 });
    const ema26Series  = chartApi.addLineSeries({ lineWidth:2 });
    const rsiSeries    = rsiApi.addLineSeries({ lineWidth:2 });

    new ResizeObserver(() => chartApi.applyOptions({ width: chartEl.clientWidth })).observe(chartEl);
    new ResizeObserver(() => rsiApi.applyOptions({ width: rsiEl.clientWidth })).observe(rsiEl);

    let ws = null; let lastCandles = [];

    function updateIndicators(){
      const { calcEMA, calcRSI } = App.indicators;
      const ema12 = calcEMA(lastCandles,12);
      const ema26 = calcEMA(lastCandles,26);
      const rsi   = calcRSI(lastCandles,14);

      $('chkEMA12').checked ? ema12Series.setData(ema12.map((v,i)=> v==null?null:{time:lastCandles[i].time, value:v}).filter(Boolean)) : ema12Series.setData([]);
      $('chkEMA26').checked ? ema26Series.setData(ema26.map((v,i)=> v==null?null:{time:lastCandles[i].time, value:v}).filter(Boolean)) : ema26Series.setData([]);
      $('chkRSI').checked   ? rsiSeries.setData(rsi.map((v,i)=> v==null?null:{time:lastCandles[i].time, value:v}).filter(Boolean))   : rsiSeries.setData([]);
    }

    async function loadChart(){
      const symbol = $('symbolSelect').value, interval = $('interval').value;
      const data = await api(`/api/klines?symbol=${symbol}&interval=${interval}&limit=300`);
      lastCandles = data.klines.map(k => ({ time: Math.floor(k.t/1000), open:k.o, high:k.h, low:k.l, close:k.c }));
      $('chkCandles').checked ? candleSeries.setData(lastCandles) : candleSeries.setData([]);
      updateIndicators(); subscribeWS(symbol, interval);
    }

    function subscribeWS(symbol, interval){
      if (ws) ws.close();
      ws = new WebSocket(`wss://stream.binance.com:9443/ws/${symbol.toLowerCase()}@kline_${interval}`);
      ws.onmessage = ev => {
        const m = JSON.parse(ev.data); if (!m.k) return;
        const k = m.k, c = { time: Math.floor(k.t/1000), open:+k.o, high:+k.h, low:+k.l, close:+k.c };
        candleSeries.update(c);
        if (lastCandles.length && lastCandles[lastCandles.length-1].time === c.time) lastCandles[lastCandles.length-1] = c; else lastCandles.push(c);
        updateIndicators();
      };
    }

    App.chart = {
      candleSeries, ema12Series, ema26Series, rsiSeries,
      loadChart, subscribeWS, updateIndicators,
      get lastCandles(){ return lastCandles; }, set lastCandles(v){ lastCandles = v; }
    };
  });
})();
