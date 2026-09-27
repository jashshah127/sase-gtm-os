/* Market context: the one module built entirely on real, public data. */

/* Smallest axis maximum whose four tick steps land on round numbers. */
function roundAxisMax(v, headroom = 1.08) {
  const target = Math.max(v * headroom, 1e-9) / 4;
  const e = Math.pow(10, Math.floor(Math.log10(target)));
  const step = [1, 1.5, 2, 2.5, 5, 10].map(k => k * e).find(s => s >= target);
  return step * 4;
}

/* Time-scaled line chart: each series has its own dates. points: [{t: day index, v, label}] */
Charts.timeLine = function (el, series, o = {}) {
  const W = widthOf(el), H = o.h || 260, m = { t: 16, r: o.endLabels ? 96 : 18, b: 30, l: o.yW || 58 };
  const pw = W - m.l - m.r, ph = H - m.t - m.b, f = o.fmt || String;
  const pts = series.flatMap(s => s.points);
  if (!pts.length) { el.innerHTML = '<p class="empty">No data yet.</p>'; return; }
  let t0 = Math.min(...pts.map(p => p.t)), t1 = Math.max(...pts.map(p => p.t));
  const pad = Math.max(20, (t1 - t0) * 0.05);
  t0 -= pad; t1 += pad;
  const x = t => m.l + ((t - t0) / (t1 - t0)) * pw;
  const max = o.max || roundAxisMax(Math.max(...pts.map(p => p.v)), 1.05);
  const y = v => m.t + ph - (clamp(v, 0, max) / max) * ph;
  let s = '';
  for (const tv of tickVals(max, 4)) {
    s += `<line class="gl" x1="${m.l}" x2="${W - m.r}" y1="${y(tv).toFixed(1)}" y2="${y(tv).toFixed(1)}"/>`;
    s += `<text class="tick" x="${m.l - 8}" y="${y(tv).toFixed(1)}" dy=".32em" text-anchor="end">${esc(f(tv))}</text>`;
  }
  for (let yr = toDate(t0).getUTCFullYear(); yr <= toDate(t1).getUTCFullYear(); yr++) {
    for (const mo of [1, 7]) {
      const t = toDay(yr, mo, 1);
      if (t < t0 || t > t1) continue;
      const lx = x(t).toFixed(1);
      s += `<line class="gl" x1="${lx}" x2="${lx}" y1="${m.t}" y2="${m.t + ph}" stroke-dasharray="2 3"/>`;
      if (mo === 1 || pw > 520) s += `<text class="tick" x="${lx}" y="${H - 9}" text-anchor="middle">${mo === 1 ? yr : 'Jul'}</text>`;
    }
  }
  for (const se of series) {
    const p = [...se.points].sort((a, b) => a.t - b.t);
    if (!p.length) continue;
    if (p.length > 1) s += `<path d="${p.map((q, i) => `${i ? 'L' : 'M'}${x(q.t).toFixed(1)},${y(q.v).toFixed(1)}`).join('')}" fill="none" stroke="${se.color}" stroke-width="2.2" stroke-linejoin="round" pointer-events="none"/>`;
    for (const q of p) s += `<circle cx="${x(q.t).toFixed(1)}" cy="${y(q.v).toFixed(1)}" r="${p.length > 1 ? 3.5 : 5.5}" fill="${se.color}" stroke="#fff" stroke-width="1.2"${tipA(`${se.name}\n${q.label}: ${f(q.v)}`)}/>`;
  }
  if (o.endLabels) {
    const labels = series.filter(se => se.points.length).map(se => {
      const last = [...se.points].sort((a, b) => a.t - b.t).pop();
      return { text: se.short || se.name, x: x(last.t) + 9, y: y(last.v) };
    }).sort((a, b) => a.y - b.y);
    for (let i = 1; i < labels.length; i++) if (labels[i].y - labels[i - 1].y < 14) labels[i].y = labels[i - 1].y + 14;
    for (const l of labels) s += `<text class="val" x="${l.x.toFixed(1)}" y="${l.y.toFixed(1)}" dy=".35em">${esc(l.text)}</text>`;
  }
  el.innerHTML = svgDoc(W, H, s, o.aria);
};

const SERIES_STYLE = {
  'Palo Alto Networks SASE ARR': { color: PAL.ultra, short: 'Palo Alto' },
  'Zscaler ARR': { color: PAL.ink, short: 'Zscaler' },
  'Fortinet Unified SASE ARR': { color: PAL.slate, short: 'Fortinet' },
  'Netskope ARR': { color: PAL.ultraMid, short: 'Netskope' },
};
const fmtStamp = s => { if (!s) return ''; const d = new Date(s); return isNaN(d) ? String(s) : `${MONTHS[d.getUTCMonth()]} ${d.getUTCDate()}, ${d.getUTCFullYear()}`; };
const precisionWord = p => (p === 'approx' ? 'about ' : p === 'floor' ? 'over ' : '');

function pendingPanel(title, entry) {
  const invalid = String(entry.status).startsWith('invalid');
  return `<section class="panel"><h3>${esc(title)}</h3>
    <p class="cap">${invalid ? `Found ${esc(entry.file)} but it failed the schema check: ${esc(String(entry.status).replace(/^invalid:\s*/, ''))}.` : `Waiting for ${esc(entry.file)}.`}</p>
    <p class="empty">Run <code>python pipeline/fetch_public_data.py</code> (built by cto from docs/cto_brief.md), then <code>python pipeline/run_all.py</code>.</p></section>`;
}

function viewMarket(root) {
  const M = D.market;
  if (!M || !M.curated) {
    root.innerHTML = '<header class="claim"><h1>Market data has not been built yet.</h1><p class="lede">Run python pipeline/market.py, then python pipeline/build_app.py.</p></header>';
    return;
  }
  const cu = M.curated, pub = M.public;
  const companies = cu.growth.filter(g => g.kind === 'company').sort((a, b) => b.growth - a.growth);
  const panw = companies.find(g => g.ticker === 'PANW');
  const mkt = cu.growth.find(g => g.kind === 'market');
  const ratio = panw && mkt && mkt.growth ? panw.growth / mkt.growth : null;
  const pace = ratio == null ? '' : ratio >= 1.75 && ratio <= 2.25 ? 'about twice as fast as' : ratio > 1.1 ? `${ratio.toFixed(1)} times as fast as` : 'about as fast as';
  const single = cu.market.facts.find(f => /single-vendor/i.test(f.metric));
  const forecast = cu.market.facts.find(f => /forecast/i.test(f.metric) && /USD/.test(f.unit));
  const kev = pub.kev.status === 'loaded' ? pub.kev.data : null;
  const series = Object.entries(cu.series).map(([name, points]) => ({ name, points, ...(SERIES_STYLE[name] || { color: PAL.slate, short: name }) }));
  const statusLine = k => {
    const e = pub[k], label = { sec: 'SEC filings', kev: 'CISA exploited vulnerabilities', census: 'Census business counts' }[k];
    if (e.status === 'loaded') return `${label}: loaded${e.fetched_at ? `, fetched ${fmtStamp(e.fetched_at)}` : ''}`;
    return `${label}: ${e.status === 'missing' ? 'waiting for data' : 'failed checks'}`;
  };
  const actions = [];
  if (single && forecast) actions.push(`Dell'Oro expects single-vendor SASE to take ${single.value}% of a $${forecast.value}B market by 2029. That makes the SD-WAN bundle a strategy, not just a win-rate tactic: it is where the market is heading.`);
  if (panw && mkt) actions.push(`Palo Alto's SASE ARR grew ${fmt.pct(panw.growth, 0)} against ${fmt.pct(mkt.growth, 0)} for the market, so it is taking share. In this book, the fastest place to keep taking it is the uncovered mid-market whitespace.`);
  actions.push(kev
    ? `CISA lists ${fmt.int(kev.total)} exploited vulnerabilities in edge and VPN products from these vendors since ${kev.first_year}, ${fmt.int(kev.ransomware_total)} tied to ransomware. Lead the renewal-timed play with the architectural argument: fewer internet-exposed appliances to patch.`
    : 'Once the CISA data is in, lead the renewal-timed play with the architectural argument: fewer internet-exposed appliances to patch.');

  root.innerHTML = `
  <header class="claim"><h1>${esc(panw && mkt ? `Palo Alto's SASE business is growing ${pace} the market, and the market is consolidating onto single-vendor platforms.` : 'Market context from public sources.')}</h1>
    <p class="lede">Everything on this page is real, public data: earnings releases, Dell'Oro press releases, SEC filings, the CISA catalog of exploited vulnerabilities, and US Census business statistics. Every figure links to its source. Companies define ARR differently, so compare direction and magnitude, not decimals.</p></header>
  <div class="grid g2">
    ${panel('mk-growth', 'Latest reported growth', 'Year over year, for the most recent period each company reported. The dashed line is SASE market growth.')}
    ${panel('mk-arr', 'ARR by vendor over time', 'Company-reported, in billions of dollars. Zscaler and Netskope report company-wide ARR; Palo Alto Networks and Fortinet report SASE-specific figures.',
      legend(series.map(s => ({ label: s.short, color: s.color }))))}
  </div>
  <div class="grid g2">
    ${panel('mk-market', 'SASE market growth by quarter', "Dell'Oro Group: year-over-year growth in manufacturer revenue. Quarters not covered by the press releases used here are omitted.")}
    <section class="panel"><h3>Market structure</h3><p class="cap">Dell'Oro Group forecasts and share figures</p>
      <dl class="dl">${cu.market.facts.map(f => `<div><dt>${esc(f.metric)} (${esc(f.period)})</dt><dd>${f.unit === 'percent' ? `${f.value}%` : `${precisionWord(f.precision)}$${f.value}B`}</dd></div>`).join('')}
      ${cu.market.quarterly.length ? (q => `<div><dt>Quarterly market size (${esc(q.period)})</dt><dd>${precisionWord(q.precision)}$${q.value.toFixed(1)}B</dd></div>`)(cu.market.quarterly[cu.market.quarterly.length - 1]) : ''}</dl>
    </section>
  </div>

  <section class="block"><h2>Competitor scoreboard</h2>
    <p class="serif narrow">The latest figure for each company and metric, transcribed from the source documents. Verify each row against its link before quoting it.</p>
    ${table([
      { h: 'Company', f: r => `<strong>${esc(r.company)}</strong>` },
      { h: 'Metric', f: r => `${esc(r.metric)}<span class="sub">${esc(r.scope)}</span>` },
      { h: 'Period', f: r => `${esc(r.fiscal_period)}<span class="sub">ended ${esc(fmtStamp(r.period_end))}</span>` },
      { h: 'Value', num: true, f: r => fmt.money(r.value * 1e6) },
      { h: 'Growth', num: true, f: r => (r.growth == null ? '–' : fmt.pct(r.growth, 0)) },
      { h: 'Source and notes', f: r => `<a href="${esc(r.source_url)}" rel="noopener">${esc(r.source_title)}</a>${r.notes ? `<span class="sub">${esc(r.notes)}</span>` : ''}` },
    ], cu.scoreboard)}
  </section>
  <aside class="action"><h3>What it means for this plan</h3><ul>${actions.map(a => `<li>${esc(a)}</li>`).join('')}</ul></aside>

  <section class="block"><h2>From public datasets</h2>
    <p class="serif narrow">These panels read files downloaded by <code>pipeline/fetch_public_data.py</code> and checked against a fixed format before anything is drawn.</p>
    <p class="cap">${['sec', 'kev', 'census'].map(statusLine).map(esc).join('<br>')}</p>
    <div class="grid" data-market-panel="sec">${pub.sec.status === 'loaded' ? secPanel(pub.sec.data) : pendingPanel('SEC filings: revenue and backlog', pub.sec)}</div>
    <div class="grid g2">
      <div data-market-panel="kev">${kev ? kevPanel() : pendingPanel('Exploited vulnerabilities in edge and VPN products', pub.kev)}</div>
      <div data-market-panel="census">${pub.census.status === 'loaded' ? censusPanel(pub.census.data) : pendingPanel('US businesses by size: the real market', pub.census)}</div>
    </div>
  </section>

  <section class="block"><h2>Sources</h2>
    <ul class="sources">${[...cu.sources, ...M.public_sources].map(s => `<li><a href="${esc(s.url)}" rel="noopener">${esc(s.title)}</a></li>`).join('')}</ul>
  </section>
  ${footer()}`;

  chart('mk-growth', el => Charts.hbar(el, companies.map(g => ({
    label: `${g.company}: ${g.metric}`, value: g.growth, color: g.ticker === 'PANW' ? PAL.ultra : PAL.slateSoft,
    tip: `${g.company}\n${g.metric}, ${g.fiscal_period}\n${fmt.pct(g.growth, 0)} year over year`,
  })), { fmt: v => fmt.pct(v, 0), max: roundAxisMax(Math.max(...companies.map(g => g.growth), mkt ? mkt.growth : 0), 1.12), labelW: 250, ref: mkt ? mkt.growth : null, refLabel: mkt ? `Market ${fmt.pct(mkt.growth, 0)}` : '', aria: 'Latest reported growth by company' }));
  chart('mk-arr', el => Charts.timeLine(el, series, { fmt: v => `$${v.toFixed(1)}B`, endLabels: true, h: 270, aria: 'ARR by vendor over time' }));
  chart('mk-market', el => Charts.vbar(el, cu.market.quarterly.map(q => q.period), [{
    name: 'Growth', values: cu.market.quarterly.map(q => q.growth), color: PAL.ultraMid,
    tips: cu.market.quarterly.map(q => `${q.period}\nMarket revenue ${precisionWord(q.precision)}$${q.value.toFixed(1)}B\nGrowth ${fmt.pct(q.growth, 0)} year over year`),
  }], { fmt: v => fmt.pct(v, 0), max: roundAxisMax(Math.max(...cu.market.quarterly.map(q => q.growth)), 1.15), valueLabels: v => fmt.pct(v, 0), h: 230, aria: 'SASE market growth by quarter' }));
  if (kev) {
    const palette = [PAL.ultra, PAL.ink, PAL.ultraMid, PAL.slate, PAL.ultraSoft, PAL.slateSoft, '#E4E8EF'];
    const vendors = Object.keys(kev.matrix);
    chart('mk-kev', el => Charts.vbar(el, kev.years.map((y, i) => (kev.last_year_partial && i === kev.years.length - 1 ? `${y} to date` : String(y))),
      vendors.map((v, i) => ({ name: v, values: kev.matrix[v], color: palette[i % palette.length] })),
      { stacked: true, fmt: v => fmt.int(v), h: 250, aria: 'Exploited edge vulnerabilities per year' }));
  }
  if (pub.census.status === 'loaded') {
    chart('mk-census', el => Charts.hbar(el, pub.census.data.segments.map(s => ({
      label: s.segment, value: s.firms, color: PAL.ultra,
      tip: `${s.segment}\n${fmt.int(s.firms)} US firms, ${fmt.int(s.employment)} employees`,
    })), { fmt: v => fmt.int(v), labelW: 130, aria: 'US firms by segment' }));
  }
}

function secPanel(rows) {
  return `<section class="panel"><h3>SEC filings: revenue and backlog</h3>
    <p class="cap">Annual revenue from 10-K filings (latest filing wins when a period was restated) and remaining performance obligations, the contracted backlog.</p>
    ${table([
      { h: 'Company', f: r => `<strong>${esc(r.company)}</strong>` },
      { h: 'Latest fiscal year end', f: r => esc(fmtStamp(r.latest_fy_end)) },
      { h: 'Revenue', num: true, f: r => fmt.money(r.revenue) },
      { h: 'Growth', num: true, f: r => (r.revenue_yoy == null ? '–' : fmt.pct(r.revenue_yoy, 0)) },
      { h: '3-year CAGR', num: true, f: r => (r.revenue_cagr3 == null ? '–' : fmt.pct(r.revenue_cagr3, 0)) },
      { h: 'Backlog (RPO)', num: true, f: r => fmt.money(r.rpo) },
      { h: 'Backlog growth', num: true, f: r => (r.rpo_yoy == null ? '–' : fmt.pct(r.rpo_yoy, 0)) },
    ], rows)}</section>`;
}

function kevPanel() {
  const k = D.market.public.kev.data;
  const vendors = Object.keys(k.matrix);
  const palette = [PAL.ultra, PAL.ink, PAL.ultraMid, PAL.slate, PAL.ultraSoft, PAL.slateSoft, '#E4E8EF'];
  return `<section class="panel"><h3>Exploited vulnerabilities in edge and VPN products</h3>
    <p class="cap">CISA's catalog of vulnerabilities confirmed exploited in the wild, by year added. Every major edge vendor appears here, Palo Alto Networks included. The case for SASE is architectural, fewer exposed appliances to patch, not a claim that one vendor's boxes are safer.</p>
    ${legend(vendors.map((v, i) => ({ label: v, color: palette[i % palette.length] })))}
    <div id="mk-kev" class="chart"></div>
    <h3 style="margin-top:14px">Most recent additions</h3>
    ${table([
      { h: 'Added', f: r => esc(fmtStamp(r.date)) },
      { h: 'Vendor', f: r => esc(r.vendor) },
      { h: 'Product', f: r => `${esc(r.product)}<span class="sub">${esc(r.cve_id)}</span>` },
      { h: 'Ransomware use', f: r => esc(r.ransomware) },
    ], k.recent.slice(0, 6))}</section>`;
}

function censusPanel(c) {
  return `<section class="panel"><h3>US businesses by size: the real market</h3>
    <p class="cap">Census Statistics of U.S. Businesses, ${c.year}, grouped into this project's segments. Basis: ${esc(c.basis)}.${c.unmapped_bands.length ? ` Size bands that span two segments were left out: ${esc(c.unmapped_bands.join(', '))}.` : ''}</p>
    <div id="mk-census" class="chart"></div>
    ${table([
      { h: 'Segment', f: s => `<strong>${esc(s.segment)}</strong>` },
      { h: 'US firms', num: true, f: s => fmt.int(s.firms) },
      { h: 'Share of firms', num: true, f: s => fmt.pct(s.share_firms, 0) },
      { h: 'Share in this book', num: true, f: s => (s.synthetic_share == null ? '–' : fmt.pct(s.synthetic_share, 0)) },
    ], c.segments)}
    <p class="cap" style="margin-top:10px">An installed base should skew larger than the market: big organizations buy enterprise firewalls first. Where this book's mix departs from that, the synthetic assumptions deserve a second look.</p></section>`;
}
