(function () {
  const $ = App.$, api = App.api;
  async function rec(){
    const symbol = $('symbolSelect').value, interval = $('interval').value;
    const r = await api(`/api/recommendations?symbol=${symbol}&interval=${interval}`);
    $('recOut').textContent = JSON.stringify(r, null, 2);
  }
  App.recs = { rec };
})();
