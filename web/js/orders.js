(function () {
  const $ = App.$;
  const api = App.api;

  let lastPreview = null;

  async function preview(){
    const symbol = $('symbolSelect').value;
    const body = {
      symbol, side: "BUY",
      quote_amount: parseFloat($('quote').value),
      sl_pct: parseFloat($('slpct').value)/100.0,
      tp_r_multiple: parseFloat($('r').value)
    };
    const r = await api(`/api/orders/preview`, { method:"POST", body: JSON.stringify(body) });
    lastPreview = r;
    $('previewOut').textContent = JSON.stringify(r, null, 2);
    $('status').innerHTML = `<span class="ok">Проверено: step=${r.step_size}, tick=${r.tick_size}, minNotional=${r.min_notional ?? '—'}</span>`;
  }

  async function confirm(){
    if(!lastPreview){ $('status').innerHTML = `<span class="err">Сначала предпросмотр.</span>`; return; }
    try{
      const r = await api(`/api/orders/confirm`, { method:"POST", body: JSON.stringify(lastPreview) });
      $('status').innerHTML = `<span class="${r.status==='FILLED'?'ok':'warn'}">ORDER: ${r.status} (id=${r.orderId||'—'}), OCO=${r.tp_orderListId||'—'}</span>`;
    }catch(e){ $('status').innerHTML = `<span class="err">${e.message}</span>`; }
  }

  App.orders = { preview, confirm };
})();
