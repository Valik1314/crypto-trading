(function () {
  const $ = App.$, api = App.api;

  async function portfolio(){
    try{
      const p = await api(`/api/portfolio/valued`);
      let html = `TOTAL: ${p.total_usdt} USDT\n\n`;
      html += "Asset   Free      Locked    Price(USDT)   Value(USDT)   Note\n";
      html += "-------------------------------------------------------------\n";
      for(const it of p.items){
        html += `${it.asset.padEnd(6)} ${it.free.padEnd(9)} ${it.locked.padEnd(9)} `
             + `${(it.price_usdt??'-').toString().padEnd(12)} `
             + `${(it.value_usdt??'-').toString().padEnd(12)} `
             + `${it.priced?'✓':'unpriced'}\n`;
      }
      $('portfolioOut').textContent = html;
    }catch(e){
      $('portfolioOut').textContent = e.message;
    }
  }
  App.portfolio = { portfolio };
})();
