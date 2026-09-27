/* Planning simulator. The engine mirrors pipeline/planning.py line for line;
   tests/check_app.py asserts both return the same attainment. */
const SEAS_M = Array.from({ length: 12 }, (_, m) => D.cfg.seasonality[Math.floor(m / 3)] / 3);
const MONTH_LABELS = ['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'];
const PI = D.planning.inputs;
const PLAYS_PTS = Math.round((D.planning.levers.bundle_pts + D.planning.levers.renewal_pts) * 10) / 10;
const planDefaults = () => ({
  growth: D.cfg.growth, prod: PI.productivity, ramp: D.cfg.rampMonths, attrition: D.cfg.attrition,
  lead: D.cfg.lead, hiresNow: 0, hiresQ2: 0, winDelta: 0, dealDelta: 0, partnerLift: 0,
});
S.plan = planDefaults();

function planRun(p) {
  const target = PI.fy26_bookings * (1 + p.growth);
  const winMult = (PI.win_rate + p.winDelta / 100) / PI.win_rate;
  const mult = winMult * (1 + p.dealDelta);
  const s = Math.pow(1 - p.attrition, 1 / 12);
  const surv = m => Math.pow(s, Math.max(0, m - 1));
  const ramp = t => (t < 0 ? 0 : Math.min(1, (t + 0.5) / p.ramp));
  const starts = PI.specialist_start_months, nEx = starts.length;
  const core = PI.core_baseline * (1 + (p.partnerLift || 0));
  const cohorts = [];
  if (p.hiresNow) cohorts.push([2 + p.lead, p.hiresNow]);
  if (p.hiresQ2) cohorts.push([3 + p.lead, p.hiresQ2]);
  const months = [];
  for (let m = 0; m < 12; m++) {
    let exist = 0;
    for (const st of starts) exist += ramp(m - st);
    exist *= surv(m);
    let back = 0;
    for (let k = 2; k < 12; k++) back += (surv(k - 1) - surv(k)) * ramp(m - (k + p.lead));
    back *= nEx;
    let nw = 0;
    for (const [st, n] of cohorts) nw += n * Math.pow(s, Math.max(0, m - st)) * ramp(m - st);
    const specCap = p.prod * SEAS_M[m] * (exist + back) * mult;
    const newCap = p.prod * SEAS_M[m] * nw * mult;
    const coreCap = core * SEAS_M[m] * mult;
    months.push({ m, fteExist: exist + back, fteNew: nw, cap: specCap + newCap + coreCap, capNew: newCap });
  }
  const act = PI.actual_by_month;
  let forecast = 0, newArr = 0;
  for (let m = 2; m < 12; m++) { forecast += months[m].cap; newArr += months[m].capNew; }
  const total = act[0] + act[1] + forecast;
  const newCost = sum(cohorts, ([st, n]) => (n * Math.max(0, 12 - st) * PI.specialist_cost) / 12);
  const runRate = sum(cohorts, ([, n]) => n) * p.prod * mult;
  return { target, total, att: total / target, gap: target - total, newArr, newCost, runRate, months, winMult };
}

function solveHires(p, cap = 60) {
  for (let h = 0; h <= cap; h++) if (planRun({ ...p, hiresNow: h }).att >= 1) return h;
  return null;
}

function planScenarios(base) {
  const lev = D.planning.levers;
  const b = { ...base, hiresNow: 0, hiresQ2: 0, winDelta: 0 };
  const withPlays = { ...b, winDelta: PLAYS_PTS };
  const recH = solveHires(withPlays), onlyH = solveHires(b);
  const defs = [
    ['Current plan', "Today's specialists, backfills for attrition, no new hires", b],
    ['Hire 6 specialists now', 'Approved this month, productive after lead time and ramp', { ...b, hiresNow: 6 }],
    ['Win-rate plays', `SD-WAN in rival deals (+${lev.bundle_pts} pts) and renewal timing (+${lev.renewal_pts} pts)`, withPlays],
    [`Recommended: plays + ${recH ?? '60+'} hires`, 'Smallest hiring plan that reaches 100% with both plays in place', { ...withPlays, hiresNow: recH ?? 60 }],
    ['Hiring only', 'Hires needed now if nothing else changes', { ...b, hiresNow: onlyH ?? 60 }],
  ];
  const baseTotal = planRun(b).total;
  return defs.map(([name, desc, p]) => { const r = planRun(p); return { name, desc, p, r, inc: r.total - baseTotal }; });
}

const PLAN_CONTROLS = [
  { group: 'Target' },
  { k: 'growth', label: 'FY27 growth target', min: 20, max: 50, step: 1, toUi: v => Math.round(v * 100), fromUi: v => v / 100, show: v => `${Math.round(v * 100)}%`, hint: `Over FY26 bookings of ${fmt.money(PI.fy26_bookings)}` },
  { group: 'Capacity' },
  { k: 'prod', label: 'Productivity per ramped specialist', min: 1200, max: 3000, step: 1, toUi: v => Math.round(v / 1000), fromUi: v => v * 1000, show: v => fmt.money(v, 2), hint: `FY26 actual: ${fmt.money(PI.productivity, 2)} a year` },
  { k: 'ramp', label: 'Ramp to full productivity', min: 3, max: 12, step: 1, toUi: v => v, fromUi: v => v, show: v => `${v} months` },
  { k: 'attrition', label: 'Annual attrition', min: 0, max: 30, step: 1, toUi: v => Math.round(v * 100), fromUi: v => v / 100, show: v => `${Math.round(v * 100)}%`, hint: 'Departures are backfilled after the lead time' },
  { k: 'lead', label: 'Hiring lead time', min: 1, max: 6, step: 1, toUi: v => v, fromUi: v => v, show: v => `${v} months`, hint: 'Approval to start date' },
  { group: 'Levers' },
  { k: 'hiresNow', label: 'Specialists approved now', min: 0, max: 40, step: 1, toUi: v => v, fromUi: v => v, show: v => String(v) },
  { k: 'hiresQ2', label: 'Specialists approved in Q2', min: 0, max: 40, step: 1, toUi: v => v, fromUi: v => v, show: v => String(v) },
  { k: 'winDelta', label: 'Win-rate change', min: -5, max: 10, step: 0.1, toUi: v => v, fromUi: v => Math.round(v * 10) / 10, show: v => fmt.pts(v), hint: `The two plays in the memo are worth +${PLAYS_PTS} pts` },
  { k: 'dealDelta', label: 'Average deal size change', min: -10, max: 20, step: 1, toUi: v => Math.round(v * 100), fromUi: v => v / 100, show: v => `${v >= 0 ? '+' : '−'}${Math.abs(Math.round(v * 100))}%` },
];

const ctlHtml = c => (c.group
  ? `<div class="ctl-group">${esc(c.group)}</div>`
  : `<div class="ctl"><label for="ctl-${c.k}"><span>${esc(c.label)}</span><output id="out-${c.k}" for="ctl-${c.k}">${esc(c.show(S.plan[c.k]))}</output></label>` +
    `<input type="range" id="ctl-${c.k}" min="${c.min}" max="${c.max}" step="${c.step}" value="${c.toUi(S.plan[c.k])}">` +
    `${c.hint ? `<div class="hint">${esc(c.hint)}</div>` : ''}</div>`);

function syncControls() {
  for (const c of PLAN_CONTROLS) {
    if (!c.k) continue;
    const inp = document.getElementById('ctl-' + c.k), out = document.getElementById('out-' + c.k);
    if (inp) inp.value = c.toUi(S.plan[c.k]);
    if (out) out.textContent = c.show(S.plan[c.k]);
  }
}

function planClaim(r, H, p) {
  const head = `At these settings, FY27 lands at ${fmt.pct(r.att, 0)} of the ${fmt.money(r.target)} target.`;
  if (r.att >= 1) return `${head} That clears it by ${fmt.money(-r.gap)}.`;
  if (H == null) return `${head} Hiring alone cannot close the gap this fiscal year.`;
  const more = H - p.hiresNow, changed = p.hiresNow || p.hiresQ2 || p.winDelta;
  return `${head} Closing ${changed ? 'the rest' : 'it'} by hiring takes ${more} ${changed ? 'more ' : ''}specialist${more === 1 ? '' : 's'} approved now.`;
}

function viewPlanning(root) {
  root.innerHTML = `
  <header class="claim"><h1 id="plan-claim"></h1>
    <p class="lede">The model runs month by month from August. August and September are actual bookings; from October it adds up specialist capacity after ramp, attrition, and backfills, plus a baseline from territories with no specialist. Move any assumption and everything below recalculates.</p></header>
  <div class="plan">
    <aside class="controls" aria-label="Assumptions">
      <h3>Assumptions</h3>
      ${PLAN_CONTROLS.map(ctlHtml).join('')}
      <div class="ctl-actions"><button class="btn primary" id="plan-rec" type="button">Load recommended plan</button><button class="btn" id="plan-reset" type="button">Reset</button></div>
    </aside>
    <div class="plan-out">
      <div class="kpis k4" id="plan-kpis"></div>
      <div class="grid">${panel('pl-cum', 'Cumulative bookings against the FY27 target', 'Solid: actual bookings through Sep 25. Dashed: modeled capacity from October.',
        legend([{ label: 'Target', color: PAL.slate, kind: 'line' }, { label: 'Actual', color: PAL.ink, kind: 'line' }, { label: 'Modeled', color: PAL.ultra, kind: 'dash' }]))}</div>
      <div class="grid g2">
        ${panel('pl-fte', 'Productive specialist capacity', 'Ramped-equivalent specialists by month, after attrition and backfills',
          legend([{ label: "Today's team and backfills", color: PAL.slateSoft }, { label: 'New hires', color: PAL.ultra }]))}
        <section class="panel" id="pl-pipe"></section>
      </div>
      <div class="grid"><section class="panel"><h3>Scenarios under these assumptions</h3>
        <p class="cap">Each row changes only hiring and win rate. Growth, productivity, ramp, attrition, and lead time come from the sliders.</p>
        <div id="pl-scn"></div></section></div>
    </div>
  </div>
  <section class="block" id="terr-block"></section>
  ${footer()}`;

  let raf = 0;
  const schedule = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(renderPlanOut); };
  for (const c of PLAN_CONTROLS) {
    if (!c.k) continue;
    const inp = document.getElementById('ctl-' + c.k);
    inp.addEventListener('input', () => {
      S.plan[c.k] = c.fromUi(parseFloat(inp.value));
      document.getElementById('out-' + c.k).textContent = c.show(S.plan[c.k]);
      schedule();
    });
  }
  $('#plan-reset').addEventListener('click', () => { S.plan = planDefaults(); syncControls(); renderPlanOut(); });
  $('#plan-rec').addEventListener('click', () => applyScenario(3));
  renderPlanOut();
  renderTerritory();
}

function applyScenario(i) {
  const sc = planScenarios(S.plan)[i];
  if (!sc) return;
  Object.assign(S.plan, { hiresNow: sc.p.hiresNow, hiresQ2: sc.p.hiresQ2, winDelta: sc.p.winDelta });
  syncControls();
  renderPlanOut();
}

function renderPlanOut() {
  const p = S.plan, r = planRun(p), H = solveHires(p);
  $('#plan-claim').textContent = planClaim(r, H, p);
  $('#plan-kpis').innerHTML = [
    kpi('plan-forecast', 'FY27 bookings, modeled', fmt.money(r.total), r.total, `Target ${fmt.money(r.target)}`),
    kpi('plan-att', 'Attainment', fmt.pct(r.att, 1), r.att, r.att >= 1 ? 'Target reached' : 'Of the FY27 target'),
    kpi('plan-gap', r.gap > 0 ? 'Gap to target' : 'Above target', fmt.money(Math.abs(r.gap)), r.gap, r.gap > 0 ? 'Still to find' : 'Headroom'),
    kpi('plan-hires', 'Hires needed now', H == null ? 'Over 60' : String(Math.max(0, H - p.hiresNow)), H, H == null ? 'Hiring alone cannot close it' : 'Beyond those already set, to reach 100%'),
  ].join('');

  const act = PI.actual_by_month;
  let t = 0;
  const tgt = SEAS_M.map(w => (t += w * r.target));
  const actual = [act[0], act[0] + act[1], ...Array(10).fill(null)];
  const model = [null, act[0] + act[1]];
  let c = act[0] + act[1];
  for (let m = 2; m < 12; m++) { c += r.months[m].cap; model.push(c); }
  chart('pl-cum', el => Charts.line(el, MONTH_LABELS, [
    { name: 'Target', values: tgt, color: PAL.slate, width: 1.6 },
    { name: 'Actual', values: actual, color: PAL.ink, width: 2.6, dots: true },
    { name: 'Modeled', values: model, color: PAL.ultra, dashed: true, width: 2.4 },
  ], { fmt: v => fmt.money(v), h: 280, labelEvery: 1, aria: 'Cumulative bookings against target' }));
  chart('pl-fte', el => Charts.vbar(el, MONTH_LABELS, [
    { name: "Today's team", values: r.months.map(x => x.fteExist), color: PAL.slateSoft, tips: r.months.map((x, i) => `${MONTH_LABELS[i]}\nToday's team and backfills: ${x.fteExist.toFixed(1)}\nNew hires: ${x.fteNew.toFixed(1)}`) },
    { name: 'New hires', values: r.months.map(x => x.fteNew), color: PAL.ultra, tips: r.months.map((x, i) => `${MONTH_LABELS[i]}\nToday's team and backfills: ${x.fteExist.toFixed(1)}\nNew hires: ${x.fteNew.toFixed(1)}`) },
  ], { stacked: true, fmt: v => v.toFixed(0), h: 250, aria: 'Productive specialist capacity by month' }));

  const dwr = D.cfg.dollarWinRate * r.winMult;
  const remaining = Math.max(0, r.target - act[0] - act[1]);
  const needed = remaining / dwr;
  const openFY = sum(OPP.filter(o => o.core && o.open && o.l >= Q1S && o.l <= qBounds(2027, 4)[1]), o => o.m);
  const gapP = Math.max(0, needed - openFY);
  const weeks = Math.max(1, Math.round((toDay(2027, 4, 30) - AS_OF) / 7));
  const recentW = sum(OPP.filter(o => o.core && o.c > AS_OF - 56 && o.c <= AS_OF), o => o.m) / 8;
  $('#pl-pipe').innerHTML = `<h3>Pipeline math</h3><p class="cap">What this plan asks of pipeline, at a ${fmt.pct(dwr, 0)} dollar win rate</p>
    <dl class="dl">
      <div><dt>Still to book in FY27</dt><dd>${fmt.money(remaining)}</dd></div>
      <div><dt>Pipeline needed to book it</dt><dd>${fmt.money(needed)}</dd></div>
      <div><dt>Open FY27 pipeline today</dt><dd>${fmt.money(openFY)}</dd></div>
      <div><dt>Pipeline still to create</dt><dd>${fmt.money(gapP)}</dd></div>
      <div><dt>Weekly creation needed through Apr 30</dt><dd>${fmt.money(gapP / weeks)} <span class="muted">vs ${fmt.money(recentW)} now</span></dd></div>
      <div><dt>FY27 cost of new hires</dt><dd>${fmt.money(r.newCost)}</dd></div>
      <div><dt>Annual capacity added once ramped</dt><dd>${fmt.money(r.runRate)}</dd></div>
    </dl>`;

  const scn = planScenarios(p);
  $('#pl-scn').innerHTML = table([
    { h: 'Scenario', f: x => `<strong>${esc(x.name)}</strong><span class="sub">${esc(x.desc)}</span>` },
    { h: 'Attainment', num: true, f: x => fmt.pct(x.r.att, 1) },
    { h: 'Added FY27 bookings', num: true, f: x => (x.inc > 0 ? '+' : '') + fmt.money(x.inc) },
    { h: 'FY27 hiring cost', num: true, f: x => fmt.money(x.r.newCost) },
    { h: 'Capacity once ramped', num: true, f: x => fmt.money(x.r.runRate) },
    { h: '', f: (x, i) => `<button class="btn small" type="button" data-apply="${i}">Apply</button>` },
  ], scn, { cls: 'scn', rowAttr: (x, i) => `data-scn="${i}" data-att="${x.r.att}"` });
  $$('[data-apply]', $('#pl-scn')).forEach(b => b.addEventListener('click', () => applyScenario(parseInt(b.dataset.apply, 10))));
}

/* ---------- Territory designer ---------- */
const terrValue = a => (a.pa ? 0.2 * Math.max(0, a.fp - a.ar) : a.ev);
function balanceTerritories(accts, k) {
  const items = accts.map(a => ({ a, v: terrValue(a) })).sort((x, y) => y.v - x.v);
  const T = Array.from({ length: k }, (_, i) => ({ i, v: 0, n: 0, accts: [] }));
  const mv = sum(items, it => it.v) / k || 1, mn = items.length / k || 1;
  for (const it of items) {
    let best = T[0], bs = Infinity;
    for (const t of T) { const score = t.v / mv + (0.35 * t.n) / mn; if (score < bs) { bs = score; best = t; } }
    best.v += it.v; best.n += 1; best.accts.push(it.a);
  }
  return T.sort((a, b) => b.v - a.v).map((t, rank) => ({ ...t, i: rank }));
}
const cvOf = arr => { const m = mean(arr); return m ? stdev(arr) / m : 0; };

function renderTerritory() {
  const box = $('#terr-block');
  if (!box) return;
  box.innerHTML = `
    <h2>Territory designer</h2>
    <p class="serif narrow">Carve a region and segment into specialist territories of equal opportunity. Accounts go largest first to whichever territory is lightest, with a penalty for account count, so no one inherits every large account. In practice, geography and named-account rules would constrain this further.</p>
    <div class="filters">
      ${selectHtml('tr-rg', 'Region', LK.regions.map((r, i) => [i, r]), S.terr.rg)}
      ${selectHtml('tr-sg', 'Segment', LK.segments.map((s, i) => [i, s]), S.terr.sg)}
      <div class="ctl" style="min-width:260px;margin:0"><label for="tr-k"><span>Specialist territories</span><output id="tr-k-out"></output></label><input type="range" id="tr-k" min="1" max="20" step="1"></div>
    </div>
    <div id="tr-out"></div>`;
  const onScope = () => { S.terr.rg = parseInt($('#tr-rg').value, 10); S.terr.sg = parseInt($('#tr-sg').value, 10); S.terr.k = null; renderTerritoryOut(); };
  $('#tr-rg').addEventListener('change', onScope);
  $('#tr-sg').addEventListener('change', onScope);
  $('#tr-k').addEventListener('input', e => { S.terr.k = parseInt(e.target.value, 10); renderTerritoryOut(); });
  renderTerritoryOut();
}

function renderTerritoryOut() {
  const T = S.terr;
  const accts = ACC.filter(a => a.rg === T.rg && a.sg === T.sg);
  const cap = D.cfg.accountsPerSpecialist[T.sg];
  const suggested = Math.max(1, Math.ceil(accts.length / cap));
  const k = clamp(T.k ?? suggested, 1, 20);
  $('#tr-k').value = k;
  $('#tr-k-out').textContent = String(k);
  const cur = new Map();
  for (const a of accts) {
    const t = cur.get(a.tr) || { id: TERR[a.tr].id, v: 0, n: 0, cv: TERR[a.tr].cv };
    t.v += terrValue(a); t.n += 1; cur.set(a.tr, t);
  }
  const curRows = [...cur.values()].sort((a, b) => b.v - a.v);
  const prop = balanceTerritories(accts, k);
  const specNow = SPEC.filter(s => s.rg === T.rg && s.sg === T.sg).length;
  const covShare = accts.length ? accts.filter(a => a.cov).length / accts.length : 0;
  const total = sum(accts, terrValue);
  const cvCur = cvOf(curRows.map(r => r.v)), cvNew = cvOf(prop.map(t => t.v));
  const topInd = t => {
    const cnt = new Map();
    for (const a of t.accts) cnt.set(a.in, (cnt.get(a.in) || 0) + 1);
    return [...cnt.entries()].sort((a, b) => b[1] - a[1]).slice(0, 2).map(([i]) => LK.industries[i]).join(', ');
  };
  $('#tr-out').innerHTML = `
    <div class="kpis k4" style="margin-top:20px">
      ${kpi('tr-accts', 'Accounts', fmt.int(accts.length), accts.length, `${fmt.pct(covShare, 0)} covered by ${specNow} specialist${specNow === 1 ? '' : 's'} today`)}
      ${kpi('tr-value', 'Opportunity value', fmt.money(total), total, 'Whitespace plus 20% of expansion room')}
      ${kpi('tr-sugg', 'Suggested specialists', String(suggested), suggested, `One per about ${cap} ${LK.segments[T.sg].toLowerCase()} accounts`)}
      ${kpi('tr-cv', 'Load imbalance', `${fmt.pct(cvCur, 0)} to ${fmt.pct(cvNew, 1)}`, cvNew, 'Spread of territory value, today versus proposed')}
    </div>
    <div class="grid g2">
      ${panel('tr-cur', 'Today: core seller territories', `${curRows.length} territories. Red means no SASE specialist.`)}
      ${panel('tr-new', 'Proposed: balanced specialist territories', `${k} territories of roughly equal value`)}
    </div>
    <div class="grid"><section class="panel"><h3>Proposed territories</h3>
      ${table([
        { h: 'Territory', f: t => `Specialist territory ${t.i + 1}` },
        { h: 'Accounts', num: true, f: t => fmt.int(t.n) },
        { h: 'Customers', num: true, f: t => fmt.int(t.accts.filter(a => a.pa).length) },
        { h: 'Opportunity value', num: true, f: t => fmt.money(t.v) },
        { h: 'Largest account', f: t => { const a = [...t.accts].sort((x, y) => terrValue(y) - terrValue(x))[0]; return a ? `${esc(a.nm)}<span class="sub">${fmt.money(terrValue(a))}</span>` : '–'; } },
        { h: 'Main industries', f: t => esc(topInd(t)) },
      ], prop)}
    </section></div>`;
  chart('tr-cur', el => Charts.hbar(el, curRows.map(r => ({ label: r.id, value: r.v, color: r.cv ? PAL.ultra : PAL.crimson, tip: `${r.id}\n${r.n} accounts, ${fmt.money(r.v)}\n${r.cv ? 'SASE specialist' : 'No SASE specialist'}` })), { fmt: v => fmt.money(v), labelW: 110, rowH: 26, aria: 'Current territory loads' }));
  chart('tr-new', el => Charts.hbar(el, prop.map(t => ({ label: `Territory ${t.i + 1}`, value: t.v, color: PAL.ultra, tip: `Territory ${t.i + 1}\n${t.n} accounts, ${fmt.money(t.v)}` })), { fmt: v => fmt.money(v), labelW: 110, rowH: 26, ref: total / k, refLabel: 'Even split', aria: 'Proposed territory loads' }));
}
