window.App = window.App || {};
App.$ = (id) => document.getElementById(id);
App.api = async (url, opts = {}) => {
  const r = await fetch(url, Object.assign({ headers: { 'Content-Type': 'application/json' } }, opts));
  if (!r.ok) throw new Error(await r.text());
  return r.json();
};
