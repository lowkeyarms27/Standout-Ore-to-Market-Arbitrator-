const BASE = '/api'

async function get(path) {
  const r = await fetch(`${BASE}${path}`)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

async function post(path, body) {
  const r = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

export const api = {
  getPricesLatest: () => get('/prices/latest'),
  getPriceHistory: (symbol, hours = 24) => get(`/prices/history/${symbol}?hours=${hours}`),
  getElecHistory: (hours = 24) => get(`/prices/history/elec/demand?hours=${hours}`),
  getMineState: () => get('/mine/state'),
  mineOverride: (body) => post('/mine/override', body),
  getAlerts: (limit = 50) => get(`/alerts?limit=${limit}`),
  getDecisions: (limit = 50) => get(`/decisions?limit=${limit}`),
  simulate: (scenario) => post('/simulate', { scenario }),
  generateReport: (report_type) => post('/reports/generate', { report_type }),
  getReports: () => get('/reports'),
}
