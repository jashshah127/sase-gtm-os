'use strict';
/*
 * SASE GTM Operating System: core data model, formatting, metrics, and state.
 * The Python pipeline in /pipeline builds the data; this file turns it back into
 * objects and recomputes every metric live, so filters and sliders just work.
 * All account, deal, and seller data is synthetic.
 */
const D = JSON.parse(document.getElementById('gtm-data').textContent);
const LK = D.lk;
const PAL = {
  ink: '#0F1B33', ink2: '#3A4760', ultra: '#2B3FE0', ultraMid: '#7B88EC', ultraSoft: '#C4CAF6',
  moss: '#2E7D5B', mossSoft: '#A7D0BC', crimson: '#C23B4E', crimsonSoft: '#E9B2BB',
  slate: '#8290A6', slateSoft: '#C3CBD8', haze: '#DCE2EC', amber: '#B7791F'
};
const STAGE_COLORS = ['#B8BFF4', '#97A1F0', '#7483EB', '#5163E6', '#2B3FE0'];

/* ---------- helpers ---------- */
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const sum = (arr, f) => { let t = 0; for (const x of arr) t += f ? f(x) : x; return t; };
const mean = arr => (arr.length ? sum(arr) / arr.length : 0);
const stdev = arr => { if (arr.length < 2) return 0; const m = mean(arr); return Math.sqrt(sum(arr, x => (x - m) ** 2) / (arr.length - 1)); };
const median = arr => { if (!arr.length) return null; const s = [...arr].sort((a, b) => a - b); const h = s.length >> 1; return s.length % 2 ? s[h] : (s[h - 1] + s[h]) / 2; };
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const rate = arr => (arr.length ? arr.filter(o => o.won).length / arr.length : null);

/* ---------- formatting ---------- */
const fmt = {
  money(v, d) {
    if (v == null || !isFinite(v)) return '–';
    const a = Math.abs(v), sg = v < 0 ? '−' : '';
    if (a >= 1e9) return `${sg}$${(a / 1e9).toFixed(d ?? 2)}B`;
    if (a >= 1e6) return `${sg}$${(a / 1e6).toFixed(d ?? 1)}M`;
    if (a >= 1e3) return `${sg}$${(a / 1e3).toFixed(d ?? 0)}K`;
    return `${sg}$${a.toFixed(0)}`;
  },
  pct: (v, d = 1) => (v == null || !isFinite(v) ? '–' : `${(v * 100).toFixed(d)}%`),
  int: v => (v == null || !isFinite(v) ? '–' : Math.round(v).toLocaleString('en-US')),
  x: (v, d = 2) => (v == null || !isFinite(v) ? '–' : `${v.toFixed(d)}x`),
  pts: (v, d = 1) => `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(d)} pts`,
};

/* ---------- calendar: Palo Alto Networks' fiscal year starts August 1 ---------- */
const DAY_MS = 86400000;
const EPOCH_MS = Date.UTC(2023, 0, 1);
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const toDate = d => new Date(EPOCH_MS + d * DAY_MS);
const toDay = (y, m, dd) => Math.round((Date.UTC(y, m - 1, dd) - EPOCH_MS) / DAY_MS);
const fmtDate = (d, year = true) => {
  if (d == null) return '–';
  const t = toDate(d);
  return `${MONTHS[t.getUTCMonth()]} ${t.getUTCDate()}${year ? ', ' + t.getUTCFullYear() : ''}`;
};
function fiscal(d) {
  const t = toDate(d), m = t.getUTCMonth() + 1, y = t.getUTCFullYear();
  return { fy: m >= 8 ? y + 1 : y, q: Math.floor(((m - 8 + 12) % 12) / 3) + 1 };
}
function qBounds(fy, q) {
  const sm = ((7 + 3 * (q - 1)) % 12) + 1;
  const sy = sm >= 8 ? fy - 1 : fy;
  let em = sm + 3, ey = sy;
  if (em > 12) { em -= 12; ey += 1; }
  return [toDay(sy, sm, 1), toDay(ey, em, 1) - 1];
}
const qLabel = (fy, q) => `FY${String(fy % 100).padStart(2, '0')} Q${q}`;

/* ---------- data ---------- */
function decode(cols) {
  const keys = Object.keys(cols), n = cols[keys[0]].length, out = new Array(n);
  for (let i = 0; i < n; i++) { const o = {}; for (const k of keys) o[k] = cols[k][i]; out[i] = o; }
  return out;
}
const ACC = decode(D.acc), OPP = decode(D.opp), TERR = decode(D.terr), SPEC = decode(D.spec);
const AS_OF = D.meta.asOf;
const [Q1S, Q1E] = qBounds(2027, 1);
ACC.forEach((a, i) => {
  a.i = i;
  a.prop = a.pr / 10000;
  a.ev = a.pa ? 0 : Math.round((a.prop * a.lp) / 100) * 100;      // propensity-weighted whitespace
  a.tier = a.is >= D.icp.cutoffs.A ? 'A' : a.is >= D.icp.cutoffs.B ? 'B' : 'C';
  a.cov = TERR[a.tr].cv;
});
OPP.forEach(o => {
  o.open = o.s <= 4; o.won = o.s === 5; o.lost = o.s === 6; o.core = o.t <= 1;
  o.fq = fiscal(o.l); o.acc = ACC[o.a];
});

/* ---------- scope and metrics (mirror pipeline/metrics.py) ---------- */
const inScope = (a, f) => (f.rg < 0 || a.rg === f.rg) && (f.sg < 0 || a.sg === f.sg) && (f.in < 0 || a.in === f.in);
function scope(f) {
  const mask = new Uint8Array(ACC.length), accs = [];
  for (const a of ACC) if (inScope(a, f)) { mask[a.i] = 1; accs.push(a); }
  return { accs, opps: OPP.filter(o => mask[o.a]), mask };
}
function scopeLabel(f) {
  const p = [];
  if (f.rg >= 0) p.push(LK.regions[f.rg]);
  if (f.sg >= 0) p.push(LK.segments[f.sg]);
  if (f.in >= 0) p.push(LK.industries[f.in]);
  return p.join(', ');
}
const createdInWeek = (opps, end) => sum(opps.filter(o => o.c > end - 7 && o.c <= end), o => o.m);

function metrics(sc) {
  const { accs, opps } = sc;
  const n = accs.length, cust = accs.filter(a => a.pa).length;
  const non = accs.filter(a => !a.pa);
  const evs = non.map(a => a.ev).sort((x, y) => y - x);
  const evTotal = sum(evs);
  let halfK = 0, cum = 0;
  for (const v of evs) { cum += v; if (cum / evTotal <= 0.5) halfK += 1; else break; }
  const core = opps.filter(o => o.core), won = core.filter(o => o.won), open = core.filter(o => o.open);
  const fy26b = sum(won.filter(o => o.fq.fy === 2026), o => o.m);
  const target = fy26b * (1 + D.cfg.growth);
  const planQ = D.cfg.seasonality.map(w => target * w);
  const qtd = sum(won.filter(o => o.l >= Q1S && o.l <= AS_OF), o => o.m);
  const elapsed = (AS_OF - Q1S + 1) / (Q1E - Q1S + 1);
  const cov = [1, 2, 3, 4].map(q => {
    const [s, e] = qBounds(2027, q);
    const pipe = sum(open.filter(o => o.l >= s && o.l <= e), o => o.m);
    const rem = planQ[q - 1] - (q === 1 ? qtd : 0);
    return { q, pipe, rem, cov: rem > 0 ? pipe / rem : null };
  });
  const landClosed = core.filter(o => o.t === 0 && (o.won || o.lost));
  const fy26land = landClosed.filter(o => o.fq.fy === 2026);
  const recent = core.filter(o => o.c > AS_OF - 56 && o.c <= AS_OF);
  return {
    n, cust, attach: n ? cust / n : null, arr: sum(accs, a => a.ar + a.ba), nonN: non.length,
    evTotal, halfK: evTotal > 0 ? halfK + 1 : 0,
    core, won, open, fy26b, target, planQ, qtd, elapsed,
    pacing: planQ[0] > 0 ? qtd / (planQ[0] * elapsed) : null, cov,
    landClosed, wr: rate(fy26land), wrN: fy26land.length,
    cyc: median(won.filter(o => o.t === 0 && o.fq.fy === 2026).map(o => o.l - o.c)),
    stalled: open.filter(o => o.s === 2 && AS_OF - o.e > D.cfg.stageSla[2]),
    pastDue: open.filter(o => o.l < AS_OF).length,
    weekly: sum(recent, o => o.m) / 8,
  };
}

/* ---------- UI helpers ---------- */
let CHARTS = [];
function chart(id, draw) {
  const el = typeof id === 'string' ? document.getElementById(id) : id;
  if (!el) return;
  CHARTS = CHARTS.filter(c => c.el.isConnected);
  CHARTS.push({ el, draw });
  draw(el);
}
const panel = (id, title, cap = '', extra = '') =>
  `<section class="panel"><h3>${esc(title)}</h3>${cap ? `<p class="cap">${cap}</p>` : ''}${extra}<div id="${id}" class="chart"></div></section>`;
function table(cols, rows, opt = {}) {
  const head = cols.map(c => `<th scope="col"${c.num ? ' class="num"' : ''}>${esc(c.h)}</th>`).join('');
  const body = rows.map((r, i) => `<tr${opt.rowAttr ? ' ' + opt.rowAttr(r, i) : ''}>${cols.map(c => `<td${c.num ? ' class="num"' : ''}>${c.f(r, i)}</td>`).join('')}</tr>`).join('');
  return `<div class="table-wrap"><table${opt.cls ? ` class="${opt.cls}"` : ''}${opt.id ? ` id="${opt.id}"` : ''}><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}
const kpi = (key, label, value, raw, sub = '') =>
  `<div class="kpi" data-kpi="${key}" data-value="${raw ?? ''}"><div class="l">${esc(label)}</div><div class="v">${esc(value)}</div><div class="s">${esc(sub)}</div></div>`;
function chip(status) {
  const cls = { 'On track': 'ok', Pass: 'ok', Watch: 'watch', 'At risk': 'risk', Quarantined: 'risk',
    'Flagged for owner update': 'watch', Flagged: 'watch' }[status] || 'neutral';
  return `<span class="chip ${cls}">${esc(status)}</span>`;
}
const legend = items => `<div class="legend">${items.map(i => `<span><i class="${i.kind || ''}" style="${i.kind ? `border-color:${i.color}` : `background:${i.color}`}"></i>${esc(i.label)}</span>`).join('')}</div>`;
function selectHtml(id, label, options, value) {
  return `<label class="field" for="${id}">${esc(label)}<select id="${id}">${options.map(([v, t]) => `<option value="${v}"${v === value ? ' selected' : ''}>${esc(t)}</option>`).join('')}</select></label>`;
}
const acctCell = a => `${esc(a.nm)}<span class="sub">${esc(LK.segments[a.sg])}, ${esc(LK.regions[a.rg])}</span>`;
const renewText = d => (d < 365 ? `in ${d} days` : `in ${(d / 365).toFixed(1)} years`);
function footer() {
  return `<footer class="foot">Independent portfolio project by ${esc(D.meta.author)}. All account, deal, and seller data is synthetic. Not affiliated with or endorsed by Palo Alto Networks; product and company names are used only to describe the market. Competitor win rates are synthetic and say nothing about any vendor's actual performance.</footer>`;
}

/* ---------- state ---------- */
const S = {
  f: { rg: -1, sg: -1, in: -1 },
  revTab: 'pipeline',
  plan: null,
  terr: { rg: 1, sg: 2, k: null },
  wbr: { week: AS_OF, rg: -1 },
  launch: { rg: -1, doc: 'icp' },
  cadence: { q: '' },
};
