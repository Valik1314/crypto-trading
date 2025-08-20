(function () {
  const $ = App.$;

  document.addEventListener('DOMContentLoaded', () => {
    const pairs = ["BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT","ADAUSDT","DOGEUSDT","TONUSDT","TRXUSDT","LINKUSDT"];
    function initSymbols(){
      const sel = $('symbolSelect'); sel.innerHTML = "";
      for(const p of pairs){ const o=document.createElement('option'); o.value=p; o.textContent=p; sel.appendChild(o); }
      sel.value = "BTCUSDT";
    }
    $('pairSearch').addEventListener('input', e=>{
      const q = e.target.value.toUpperCase();
      const sel = $('symbolSelect');
      [...sel.options].forEach(opt => opt.style.display = opt.value.includes(q) ? "block" : "none");
    });

    $('load').onclick    = () => App.chart.loadChart();
    $('rec').onclick     = () => App.recs.rec();
    $('pf').onclick      = () => App.portfolio.portfolio();

    $('chkCandles').onchange = () => {
      $('chkCandles').checked ? App.chart.candleSeries.setData(App.chart.lastCandles)
                              : App.chart.candleSeries.setData([]);
    };
    $('chkEMA12').onchange = () => App.chart.updateIndicators();
    $('chkEMA26').onchange = () => App.chart.updateIndicators();
    $('chkRSI').onchange   = () => App.chart.updateIndicators();

    initSymbols();
    (async()=>{ await App.chart.loadChart(); await App.recs.rec(); })();
  });
})();
