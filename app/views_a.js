/* Briefing and Revenue intelligence views. */
const REV_TABS = [['pipeline', 'Pipeline health'], ['whitespace', 'Attach and whitespace'], ['winloss', 'Win and loss'], ['trends', 'Trends']];
const SEG_SHORT = ['Large Ent.', 'Enterprise', 'Mid-Market', 'Commercial'];

/* ================= Briefing: the answer on one page ================= */
function viewBriefing(root) {
  const s = D.summary, p = D.planning, lev = p.levers, de = s.deal_effects;
  const unc = s.coverage_gap.by_coverage.find(g => g.covered === 0);
  const cov = s.coverage_gap.by_coverage.find(g => g.covered === 1);
  const rec = p.scenarios.find(x => x.name.startsWith('Recommended'));
  const hireOnly = p.scenarios.find(x => x.name === 'Hiring only');
  const plays = p.scenarios.find(x => x.name === 'Win-rate plays');
  const q2 = s.pipeline_coverage[1];
  const recHires = rec.params.hires_now;
  const wk = sum(OPP.filter(o => o.core && o.c > AS_OF - 56 && o.c <= AS_OF), o => o.m) / 8;
  const finding = (fig, label, text, href, link) =>
    `<article class="finding"><div><div class="fig">${esc(fig)}</div><div class="fl">${esc(label)}</div></div>` +
    `<div><p>${text}</p><a href="${href}">${esc(link)}</a></div></article>`;

  const recRows = [
    { a: 'Make SD-WAN the default in every Zscaler and Netskope deal', o: 'Product Marketing, Sales', t: 'Q2 kickoff', w: `+${lev.bundle_pts} pts of blended win rate` },
    { a: 'Run a renewal-timed attach play for accounts renewing their firewall in 90 to 270 days', o: 'GTM Strategy, Sales Ops', t: 'October', w: `+${lev.renewal_pts} pts of blended win rate` },
    { a: `Approve ${recHires} SASE specialists for JAPAC and EMEA mid-market`, o: 'Sales leadership, Finance', t: 'This month', w: `${fmt.money(rec.new_hire_run_rate)} a year once ramped, for ${fmt.money(rec.new_hire_cost_fy27)} in FY27` },
    { a: 'Run a Q2 pipeline sprint with Marketing and Partners', o: 'Marketing, Partners', t: 'Through mid-November', w: `Weekly creation from ${fmt.money(wk)} to ${fmt.money(wk + 1e6)}` },
  ];
  const mapRows = [
    ['Market sizing and competitive context', '#market', 'Market context', 'Real public data: competitor ARR, SASE market growth, SEC filings, exploited VPN vulnerabilities, US business counts'],
    ['Performance analytics and revenue opportunities', '#revenue', 'Revenue intelligence', 'Pipeline health, attach, whitespace ranking, win and loss with statistical controls'],
    ['GTM strategy and planning', '#planning', 'Planning simulator', 'Capacity model with ramp, attrition, and backfills; hiring solver; territory designer'],
    ['Product launch and field enablement', '#launch', 'Prisma Browser launch', 'ICP validated out of time, Tier A target list, launch scorecard, field kit'],
    ['Executive presentations and dashboards', '#exec', 'Executive layer', 'Self-drafting weekly business review and a one-page memo'],
    ['Cross-functional operating cadence and mentoring', '#cadence', 'Operating cadence', 'Metric dictionary, operating rhythm, RACI, data-quality gate, analyst onboarding'],
  ];
  const grounding = [2, 1, 3, 0].map(i => D.sources[i]).filter(Boolean);

  root.innerHTML = `
  <header class="claim hero">
    <h1>The SASE opportunity in this firewall base is a coverage problem, not a demand problem.</h1>
    <p class="lede">One in four firewall accounts runs Prisma Access. Where a SASE specialist covers the territory, attach is ${fmt.pct(cov.actual_attach)}. Where none does, it is ${fmt.pct(unc.actual_attach)}, against a modeled ${fmt.pct(unc.modeled_attach)} for the same kinds of accounts. FY27 needs ${fmt.money(s.fy27_target)} of SASE bookings, 35% more than FY26. Here is where it comes from.</p>
  </header>
  <section class="findings" aria-label="Key findings">
    ${finding(fmt.int(unc.latent_customers), 'customers missing from territories with no SASE specialist',
      `Uncovered territories attach at ${fmt.pct(unc.actual_attach)}; a model trained where coverage is good expects ${fmt.pct(unc.modeled_attach)}. The gap is widest in JAPAC and EMEA mid-market and commercial, which hold ${fmt.pct(s.coverage_gap.uncovered_share_of_ev, 0)} of all propensity-weighted whitespace.`,
      '#revenue/whitespace', 'Open the coverage gap')}
    ${finding(`${fmt.pct(de.adj_win_sse_no_bundle, 0)} to ${fmt.pct(de.adj_win_sse_bundle, 0)}`, 'win rate against Zscaler and Netskope once SD-WAN is in the deal',
      `The lift survives controls for coverage, segment, renewal timing, and source, yet only ${fmt.pct(lev.bundle_share_in_sse_now, 0)} of those deals include SD-WAN today. Timing matters too: deals opened 90 to 270 days before the firewall renewal win ${fmt.pct(de.adj_win_aligned, 0)}, against ${fmt.pct(de.adj_win_not_aligned, 0)}.`,
      '#revenue/winloss', 'Open win and loss')}
    ${finding(fmt.x(q2.coverage), 'Q2 pipeline coverage',
      `Q1 is pacing ${fmt.pct(s.q1_pacing, 0)} of plan, so this quarter is not the problem. Pipeline closing next quarter covers only ${fmt.x(q2.coverage)} of Q2's ${fmt.money(s.fy27_plan_by_quarter[1])} plan, where about 2x is healthy at this point.`,
      '#exec', 'Open the weekly review')}
  </section>

  <section class="block">
    <h2>What I would do</h2>
    ${table([
      { h: 'Action', f: r => `<strong>${esc(r.a)}</strong>` },
      { h: 'Owners', f: r => esc(r.o) },
      { h: 'When', f: r => esc(r.t) },
      { h: 'Worth', f: r => esc(r.w) },
    ], recRows, { cls: 'recs' })}
  </section>

  <section class="block split">
    <div>
      <h2>What it adds up to</h2>
      <p class="serif">Current capacity reaches ${fmt.pct(p.baseline.attainment, 0)} of the FY27 target. Hiring alone would take ${hireOnly.params.hires_now} specialists and ${fmt.money(hireOnly.new_hire_cost_fy27)} this year. The two plays reach ${fmt.pct(plays.attainment, 0)} at no headcount cost, and with ${recHires} hires the plan reaches ${fmt.pct(rec.attainment, 0)}.</p>
      <p class="serif"><a href="#planning">Change the assumptions in the planning simulator</a> or <a href="docs/executive_memo.pdf">read the one-page memo</a>.</p>
    </div>
    ${panel('ch-scen', 'Modeled FY27 attainment by plan', 'Share of the FY27 bookings target reached by each option')}
  </section>

  <section class="block">
    <h2>How this maps to the role</h2>
    ${table([
      { h: 'Responsibility in the job description', f: r => esc(r[0]) },
      { h: 'Where it lives', f: r => `<a href="${r[1]}">${esc(r[2])}</a>` },
      { h: 'What to look at', f: r => esc(r[3]) },
    ], mapRows)}
  </section>

  <section class="block">
    <h2>Grounded in public figures</h2>
    <p class="serif narrow">Every account, deal, and seller here is synthetic. The book is calibrated to Palo Alto Networks' reported scale and growth so the patterns look like the real business, not a toy. The <a href="#market">Market context</a> page uses only real, public data.</p>
    <ul class="sources">${grounding.map(g => `<li>${esc(g.fact)}. <a href="${esc(g.url)}" rel="noopener">${esc(g.source)}</a></li>`).join('')}</ul>
  </section>
  ${footer()}`;

  chart('ch-scen', el => Charts.hbar(el, p.scenarios.map(x => ({
    label: x.name, value: x.attainment,
    color: x.attainment >= 1 ? PAL.moss : x.name === 'Current plan' ? PAL.slate : PAL.ultra,
    tip: `${x.name}\n${fmt.pct(x.attainment)} of target\n${x.description}`,
  })), { fmt: v => fmt.pct(v, 0), max: 1.2, ref: 1, refLabel: 'Target', labelW: 230, aria: 'Modeled FY27 attainment by plan' }));
}

/* ================= Revenue intelligence ================= */
function revClaim(M, f) {
  if (!M.n) return 'No accounts match these filters.';
  const lab = scopeLabel(f);
  return `${lab ? lab + ': ' : ''}${fmt.pct(M.attach)} of ${fmt.int(M.n)} firewall accounts run Prisma Access. Half of the remaining ${fmt.money(M.evTotal)} in whitespace sits in ${fmt.int(M.halfK)} accounts.`;
}

function revLede(M, sc) {
  const unc = sc.accs.filter(a => !a.cov), cov = sc.accs.filter(a => a.cov);
  const at = arr => mean(arr.map(a => a.pa)), md = arr => mean(arr.map(a => a.prop));
  let t;
  if (unc.length >= 30 && cov.length >= 30) t = `Accounts with a SASE specialist attach at ${fmt.pct(at(cov))}; accounts without one attach at ${fmt.pct(at(unc))}, against a modeled ${fmt.pct(md(unc))}.`;
  else if (unc.length >= 30) t = `No SASE specialist covers most of these accounts. They attach at ${fmt.pct(at(unc))}, against a modeled ${fmt.pct(md(unc))}.`;
  else t = `A SASE specialist covers these accounts, and attach runs ${fmt.pct(at(cov))} against a modeled ${fmt.pct(md(cov))}.`;
  const q2 = M.cov[1];
  if (M.pacing != null) t += ` Q1 bookings are at ${fmt.pct(M.pacing, 0)} of straight-line plan, and next quarter's pipeline covers ${fmt.x(q2.cov)} of its plan.`;
  return t;
}

function revKpis(M) {
  const q2 = M.cov[1];
  return [
    kpi('attach', 'SASE attach', fmt.pct(M.attach), M.attach, `${fmt.int(M.cust)} of ${fmt.int(M.n)} accounts`),
    kpi('arr', 'SASE ARR', fmt.money(M.arr), M.arr, 'Access, SD-WAN, and Browser'),
    kpi('qtd', 'Q1 bookings to date', fmt.money(M.qtd), M.qtd, M.pacing == null ? 'No plan in this scope' : `${fmt.pct(M.pacing, 0)} of straight-line plan`),
    kpi('q2cov', 'Q2 pipeline coverage', fmt.x(q2.cov), q2.cov, `${fmt.money(q2.pipe)} against ${fmt.money(q2.rem)} of plan`),
    kpi('winrate', 'Land win rate, FY26', fmt.pct(M.wr), M.wr, `${fmt.int(M.wrN)} closed first-purchase deals`),
    kpi('cycle', 'Median sales cycle', M.cyc == null ? '–' : `${Math.round(M.cyc)} days`, M.cyc, 'Won land deals, FY26'),
  ].join('');
}

function viewRevenue(root, focusId) {
  const f = S.f, sc = scope(f), M = metrics(sc);
  const opts = arr => [[-1, 'All'], ...arr.map((x, i) => [i, x])];
  const filtered = f.rg >= 0 || f.sg >= 0 || f.in >= 0;
  root.innerHTML = `
  <div class="filters" role="group" aria-label="Filters">
    ${selectHtml('f-rg', 'Region', opts(LK.regions), f.rg)}
    ${selectHtml('f-sg', 'Segment', opts(LK.segments), f.sg)}
    ${selectHtml('f-in', 'Industry', opts(LK.industries), f.in)}
    ${filtered ? '<button class="btn ghost" id="f-reset" type="button">Clear filters</button>' : ''}
  </div>
  <header class="claim"><h1 id="rev-claim">${esc(revClaim(M, f))}</h1>${M.n ? `<p class="lede">${esc(revLede(M, sc))}</p>` : ''}</header>
  ${M.n ? `<div class="kpis k6">${revKpis(M)}</div>
  <div class="tabs" role="tablist" aria-label="Revenue views">${REV_TABS.map(([id, name]) =>
    `<button class="tab" role="tab" id="tab-${id}" aria-selected="${S.revTab === id}" aria-controls="rev-body" data-tab="${id}" type="button">${name}</button>`).join('')}</div>
  <div id="rev-body" role="tabpanel"></div>` : '<p class="empty">Clear a filter to see results.</p>'}
  ${footer()}`;

  ['rg', 'sg', 'in'].forEach(k => $('#f-' + k, root).addEventListener('change', e => {
    S.f[k] = parseInt(e.target.value, 10);
    viewRevenue(root, 'f-' + k);
  }));
  const reset = $('#f-reset', root);
  if (reset) reset.addEventListener('click', () => { S.f = { rg: -1, sg: -1, in: -1 }; viewRevenue(root, 'f-rg'); });
  if (focusId) { const el = document.getElementById(focusId); if (el) el.focus(); }
  if (!M.n) return;
  $$('.tab', root).forEach(b => b.addEventListener('click', () => {
    S.revTab = b.dataset.tab;
    history.replaceState(null, '', '#revenue/' + S.revTab);
    $$('.tab', root).forEach(t => t.setAttribute('aria-selected', String(t === b)));
    renderRevTab(sc, M);
  }));
  renderRevTab(sc, M);
}

function renderRevTab(sc, M) {
  const body = $('#rev-body');
  if (!body) return;
  const fn = { pipeline: revPipeline, whitespace: revWhitespace, winloss: revWinLoss, trends: revTrends }[S.revTab] || revPipeline;
  fn(body, sc, M);
}

/* ---------- Pipeline health ---------- */
function revPipeline(body, sc, M) {
  const byStage = LK.stages.slice(0, 5).map((st, i) => {
    const os = M.open.filter(o => o.s === i);
    return { label: st, value: sum(os, o => o.m), n: os.length };
  });
  const weeks = [];
  for (let k = 25; k >= 0; k--) { const end = AS_OF - 7 * k; weeks.push({ end, v: createdInWeek(M.core, end) }); }
  const trail = weeks.map(w => { const prior = []; for (let j = 1; j <= 8; j++) prior.push(createdInWeek(M.core, w.end - 7 * j)); return mean(prior); });
  const stalled = [...M.stalled].sort((a, b) => b.m - a.m);
  const q2 = M.cov[1], need2x = Math.max(0, 2 * q2.rem - q2.pipe);
  const actions = [];
  if (stalled.length) actions.push(`Walk the ${stalled.length} stalled proof-of-value deals (${fmt.money(sum(stalled, o => o.m))}) in Tuesday's forecast call. The five largest get a packaged 30-day POV plan and a named SE.`);
  if (need2x > 0) actions.push(`Q2 needs about ${fmt.money(need2x)} more pipeline to reach 2x coverage. At ${fmt.money(M.weekly)} a week today, that means a creation sprint through mid-November, weighted to mid-market deals short enough to close inside the quarter.`);
  if (M.pastDue) actions.push(`Clear ${M.pastDue} past-due close dates before the forecast snapshot so the Q1 call reflects reality.`);

  body.innerHTML = `
  <div class="grid g2">
    ${panel('rp-stage', 'Open pipeline by stage', 'Land and expansion deals, all close dates')}
    ${panel('rp-cov', 'Coverage by quarter', 'Open pipeline closing in the quarter divided by plan still to book. Read the current and next quarter first; later quarters fill in as sellers create deals.')}
  </div>
  <div class="grid">${panel('rp-weekly', 'Pipeline created per week', 'Last 26 weeks, ending Fridays. The line is the trailing 8-week average, the baseline the weekly review flags against.')}</div>
  <div class="grid"><section class="panel"><h3>Stalled in Technical Validation</h3>
    <p class="cap">${stalled.length} open deals past the 45-day proof-of-value service level, worth ${fmt.money(sum(stalled, o => o.m))}. Largest ten shown.</p>
    ${stalled.length ? table([
      { h: 'Account', f: o => acctCell(o.acc) },
      { h: 'Amount', num: true, f: o => fmt.money(o.m) },
      { h: 'Days in stage', num: true, f: o => fmt.int(AS_OF - o.e) },
      { h: 'Competitor', f: o => esc(LK.competitors[o.k]) },
      { h: 'Pushes', num: true, f: o => String(o.u) },
      { h: 'Close date', f: o => esc(fmtDate(o.l)) },
    ], stalled.slice(0, 10)) : '<p class="empty">No stalled deals in this scope.</p>'}
  </section></div>
  ${actions.length ? `<aside class="action"><h3>What I would do</h3><ul>${actions.map(a => `<li>${esc(a)}</li>`).join('')}</ul></aside>` : ''}`;

  chart('rp-stage', el => Charts.hbar(el, byStage.map((r, i) => ({ ...r, color: STAGE_COLORS[i], tip: `${r.label}\n${fmt.money(r.value)} in ${r.n} deals` })),
    { fmt: v => fmt.money(v), labelW: 170, aria: 'Open pipeline by stage' }));
  chart('rp-cov', el => Charts.vbar(el, ['Rest of Q1', 'Q2', 'Q3', 'Q4'], [{
    name: 'Coverage',
    values: M.cov.map(c => c.cov ?? 0),
    labels: M.cov.map(c => (c.cov == null ? 'Plan met' : fmt.x(c.cov))),
    colors: M.cov.map((c, i) => (i > 1 ? PAL.slateSoft : c.cov == null || c.cov >= 2 ? PAL.moss : c.cov >= 1 ? PAL.amber : PAL.crimson)),
    tips: M.cov.map((c, i) => `FY27 Q${i + 1}\n${fmt.money(c.pipe)} of pipeline against ${fmt.money(Math.max(0, c.rem))} still to book\nCoverage ${c.cov == null ? 'n/a' : fmt.x(c.cov)}`),
  }], { fmt: v => fmt.x(v, 1), refs: [{ value: 2, label: '2x' }], valueLabels: v => fmt.x(v), h: 250, aria: 'Pipeline coverage by quarter' }));
  chart('rp-weekly', el => Charts.vbar(el, weeks.map(w => fmtDate(w.end, false)), [{
    name: 'Created', values: weeks.map(w => w.v), color: PAL.ultraMid,
    tips: weeks.map((w, i) => `Week ending ${fmtDate(w.end, false)}\nCreated ${fmt.money(w.v)}\n8-week average ${fmt.money(trail[i])}`),
  }], { fmt: v => fmt.money(v), labelEvery: 4, lines: [{ values: trail, color: PAL.ink, width: 1.8 }], h: 240, aria: 'Pipeline created per week' }));
}

/* ---------- Attach and whitespace ---------- */
function revWhitespace(body, sc, M) {
  const f = S.f;
  const accR = ACC.filter(a => f.rg < 0 || a.rg === f.rg);
  const cells = LK.industries.map((ind, ii) => LK.segments.map((sg, si) => {
    const as = accR.filter(a => a.in === ii && a.sg === si), c = as.filter(a => a.pa).length;
    const v = as.length ? c / as.length : 0;
    return { v, n: as.length, tip: `${ind}, ${sg}\nAttach ${fmt.pct(v)} (${c} of ${as.length})` };
  }));
  const byT = new Map();
  for (const a of ACC) { if (!byT.has(a.tr)) byT.set(a.tr, []); byT.get(a.tr).push(a); }
  const pts = TERR.map((t, ti) => {
    if ((f.rg >= 0 && t.rg !== f.rg) || (f.sg >= 0 && t.sg !== f.sg)) return null;
    const as = byT.get(ti) || [];
    if (as.length < 8) return null;
    const act = mean(as.map(a => a.pa)), mod = mean(as.map(a => a.prop));
    return { x: mod, y: act, r: 3 + Math.sqrt(as.length) * 0.55, color: t.cv ? PAL.ultra : PAL.crimson,
      tip: `${t.id}\n${as.length} accounts, ${t.cv ? 'SASE specialist' : 'no SASE specialist'}\nActual ${fmt.pct(act)}, modeled ${fmt.pct(mod)}` };
  }).filter(Boolean);
  const axMax = Math.min(1, Math.ceil(Math.max(0.05, ...pts.map(p => Math.max(p.x, p.y))) * 1.08 * 10) / 10);
  const non = sc.accs.filter(a => !a.pa);
  const playRows = LK.plays.map((pl, i) => ({ label: pl, value: sum(non.filter(a => a.pl === i), a => a.ev), n: non.filter(a => a.pl === i).length }))
    .filter(r => r.n > 0).sort((a, b) => b.value - a.value);
  const top = [...non].sort((a, b) => b.ev - a.ev);
  const top100 = top.slice(0, 100);
  const nRenew = top100.filter(a => a.rn >= 90 && a.rn <= 270).length;
  const nSSE = top100.filter(a => a.ic >= 2).length;
  const latent = Math.round(sum(sc.accs.filter(a => !a.cov), a => a.prop - a.pa));
  const lift = D.model.lift;
  const actions = [
    `Start with the ${fmt.int(M.halfK)} accounts that hold half the whitespace. ${nRenew} of the top 100 renew their firewall in 90 to 270 days, so they get the renewal-timed play first.`,
    `${nSSE} of the top 100 run a competitor's SSE today. Lead those with the SD-WAN bundle, where the win-rate lift is largest.`,
  ];
  if (latent > 5) actions.push(`About ${latent} customers are missing in uncovered territories in this scope. That is the case for specialist coverage, sized in the planning simulator.`);

  body.innerHTML = `
  <div class="grid g2">
    ${panel('rw-heat', 'Attach rate by industry and segment', `Share of firewall accounts running Prisma Access${f.rg >= 0 ? ', ' + LK.regions[f.rg] + ' only' : ''}. The region filter applies here; segment and industry filters do not.`)}
    ${panel('rw-scatter', 'Modeled versus actual attach, by territory', 'Each dot is a core territory, sized by accounts (territories under 8 accounts hidden). Dots below the line have fewer customers than the model expects.',
      legend([{ label: 'SASE specialist', color: PAL.ultra }, { label: 'No SASE specialist', color: PAL.crimson }]))}
  </div>
  <div class="grid g2">
    ${panel('rw-play', 'Propensity-weighted whitespace by play', `${fmt.money(M.evTotal)} across ${fmt.int(non.length)} non-customers in scope`)}
    ${panel('rw-lift', 'Model check: attach by propensity decile', `Out-of-fold predictions on covered accounts. The top decile attaches at ${D.model.topDecileLift}x the average; cross-validated AUC ${D.model.auc.toFixed(2)}.`)}
  </div>
  <div class="grid"><section class="panel"><h3>Top whitespace accounts</h3>
    <p class="cap">Ranked by expected value: propensity times first-year land potential. Plays come from incumbent, renewal timing, and footprint.</p>
    ${top.length ? table([
      { h: 'Account', f: a => `${esc(a.nm)}<span class="sub">${esc(LK.industries[a.in])}</span>` },
      { h: 'Segment', f: a => esc(LK.segments[a.sg]) },
      { h: 'Region', f: a => esc(LK.regions[a.rg]) },
      { h: 'Propensity', num: true, f: a => fmt.pct(a.prop, 0) },
      { h: 'Land potential', num: true, f: a => fmt.money(a.lp) },
      { h: 'Expected value', num: true, f: a => fmt.money(a.ev) },
      { h: 'Firewall renewal', f: a => esc(renewText(a.rn)) },
      { h: 'Play', f: a => esc(LK.plays[a.pl] || '') },
    ], top.slice(0, 15)) : '<p class="empty">Every account in this scope already runs Prisma Access.</p>'}
  </section></div>
  <aside class="action"><h3>What I would do</h3><ul>${actions.map(a => `<li>${esc(a)}</li>`).join('')}</ul></aside>`;

  chart('rw-heat', el => Charts.heat(el, LK.industries, SEG_SHORT, cells, { fmt: v => fmt.pct(v, 0), domain: [0, 0.6], aria: 'Attach rate by industry and segment' }));
  chart('rw-scatter', el => Charts.scatter(el, pts, { xMax: axMax, yMax: axMax, xFmt: v => fmt.pct(v, 0), yFmt: v => fmt.pct(v, 0), diagonal: true, xLabel: 'Modeled attach', yLabel: 'Actual attach', h: 320, aria: 'Modeled versus actual attach by territory' }));
  chart('rw-play', el => Charts.hbar(el, playRows.map(r => ({ ...r, color: PAL.ultra, tip: `${r.label}\n${fmt.money(r.value)} across ${r.n} accounts` })), { fmt: v => fmt.money(v), labelW: 180, aria: 'Whitespace by play' }));
  chart('rw-lift', el => Charts.vbar(el, lift.map(l => String(l.decile)), [{
    name: 'Attach', values: lift.map(l => l.attach_rate), colors: lift.map((l, i) => (i < 3 ? PAL.ultra : PAL.ultraSoft)),
    tips: lift.map(l => `Decile ${l.decile}\nAttach ${fmt.pct(l.attach_rate)} (${l.adopters} of ${l.accounts})\nCumulative capture ${fmt.pct(l.cum_capture, 0)}`),
  }], { fmt: v => fmt.pct(v, 0), refs: [{ value: D.model.trainRate, label: 'Average' }], h: 250, aria: 'Attach by propensity decile' }));
}

/* ---------- Win and loss ---------- */
function revWinLoss(body, sc, M) {
  const land = M.landClosed;
  if (!land.length) { body.innerHTML = '<p class="empty">No closed land deals in this scope.</p>'; return; }
  const comps = LK.competitors.map((c, ci) => {
    const d = land.filter(o => o.k === ci);
    return { c: c === 'No competitor' ? 'None' : c, nb: d.filter(o => !o.b), wb: d.filter(o => o.b) };
  });
  const lost = land.filter(o => o.lost);
  const stageRows = [1, 2, 3, 4].map(si => { const n = lost.filter(o => o.x === si).length; return { label: LK.stages[si], value: lost.length ? n / lost.length : 0, n }; });
  const reasonRows = LK.lossReasons.map((r, ri) => { const n = lost.filter(o => o.r === ri).length; return { label: r, value: lost.length ? n / lost.length : 0, n }; })
    .filter(r => r.n > 0).sort((a, b) => b.value - a.value);
  const sse = land.filter(o => o.k === 0 || o.k === 1);
  const mmcom = land.filter(o => o.acc.sg >= 2);
  const factors = [
    ['SD-WAN in the deal, against Zscaler or Netskope', sse.filter(o => o.b), sse.filter(o => !o.b)],
    ['Opened 90 to 270 days before the firewall renewal', land.filter(o => o.n), land.filter(o => !o.n)],
    ['A SASE specialist covers the territory', land.filter(o => o.acc.cov), land.filter(o => !o.acc.cov)],
    ['Partner-sourced, mid-market and commercial', mmcom.filter(o => o.o === 2), mmcom.filter(o => o.o !== 2)],
  ].map(([label, a, b]) => ({ label, w: rate(a), wo: rate(b), na: a.length, nb: b.length }));
  const sseLost = sse.filter(o => o.lost);
  const tvShare = sseLost.length ? sseLost.filter(o => o.x === 2).length / sseLost.length : null;
  const f0 = factors[0], f1 = factors[1];
  const actions = [];
  if (f0.w != null && f0.wo != null) actions.push(`Make SD-WAN part of every Zscaler and Netskope proposal. Bundled deals win ${fmt.pct(f0.w, 0)} against ${fmt.pct(f0.wo, 0)} here.`);
  if (tvShare != null) actions.push(`Put competitive POVs on a 30-day plan with written success criteria: ${fmt.pct(tvShare, 0)} of losses to SSE rivals happen in Technical Validation.`);
  if (f1.w != null && f1.wo != null) actions.push(`Start SASE conversations 90 to 270 days before the firewall renewal. Those deals win ${fmt.pct(f1.w, 0)} against ${fmt.pct(f1.wo, 0)}.`);

  body.innerHTML = `
  <div class="grid g2">
    ${panel('rl-comp', 'Win rate by competitor, with and without SD-WAN', `${fmt.int(land.length)} closed land deals since FY24 Q1. Competitor names are real so the analysis reads realistically; the win rates are synthetic.`,
      legend([{ label: 'Without SD-WAN', color: PAL.slateSoft }, { label: 'With SD-WAN', color: PAL.ultra }]))}
    ${panel('rl-stage', 'Where lost deals exit', `Share of ${fmt.int(lost.length)} lost land deals, by the stage they died in`)}
  </div>
  <div class="grid g2">
    ${panel('rl-reason', 'Loss reasons', 'Share of lost land deals')}
    <section class="panel"><h3>What moves win rate</h3><p class="cap">Raw rates in this scope. Across the whole book, the SD-WAN effect holds after controlling for coverage, segment, timing, and source.</p>
    ${table([
      { h: 'Factor', f: r => esc(r.label) },
      { h: 'With', num: true, f: r => fmt.pct(r.w, 0) },
      { h: 'Without', num: true, f: r => fmt.pct(r.wo, 0) },
      { h: 'Difference', num: true, f: r => (r.w == null || r.wo == null ? '–' : fmt.pts((r.w - r.wo) * 100, 0)) },
      { h: 'Deals', num: true, f: r => fmt.int(r.na + r.nb) },
    ], factors)}</section>
  </div>
  ${actions.length ? `<aside class="action"><h3>What I would do</h3><ul>${actions.map(a => `<li>${esc(a)}</li>`).join('')}</ul></aside>` : ''}`;

  chart('rl-comp', el => Charts.vbar(el, comps.map(c => c.c), [
    { name: 'Without SD-WAN', values: comps.map(c => rate(c.nb) ?? 0), color: PAL.slateSoft, tips: comps.map(c => `${c.c}, without SD-WAN\n${c.nb.length ? fmt.pct(rate(c.nb)) : 'no deals'} of ${c.nb.length} deals`) },
    { name: 'With SD-WAN', values: comps.map(c => rate(c.wb) ?? 0), color: PAL.ultra, tips: comps.map(c => `${c.c}, with SD-WAN\n${c.wb.length ? fmt.pct(rate(c.wb)) : 'no deals'} of ${c.wb.length} deals`) },
  ], { fmt: v => fmt.pct(v, 0), max: 1, h: 260, aria: 'Win rate by competitor and SD-WAN bundle' }));
  chart('rl-stage', el => Charts.hbar(el, stageRows.map(r => ({ ...r, color: r.label === 'Technical Validation' ? PAL.crimson : PAL.slate, tip: `${r.label}\n${fmt.pct(r.value)} of lost deals (${r.n})` })), { fmt: v => fmt.pct(v, 0), labelW: 170, aria: 'Loss stage' }));
  chart('rl-reason', el => Charts.hbar(el, reasonRows.map(r => ({ ...r, color: PAL.slate, tip: `${r.label}\n${fmt.pct(r.value)} of lost deals (${r.n})` })), { fmt: v => fmt.pct(v, 0), labelW: 190, aria: 'Loss reasons' }));
}

/* ---------- Trends ---------- */
function revTrends(body, sc, M) {
  const qs = [];
  for (let fy = 2024; fy <= 2027; fy++) for (let q = 1; q <= 4; q++) if (!(fy === 2027 && q > 1)) qs.push([fy, q]);
  const inQ = (o, fy, q) => o.fq.fy === fy && o.fq.q === q;
  const land = qs.map(([fy, q]) => sum(M.won.filter(o => o.t === 0 && inQ(o, fy, q)), o => o.m));
  const exp = qs.map(([fy, q]) => sum(M.won.filter(o => o.t === 1 && inQ(o, fy, q)), o => o.m));
  const labels = qs.map(([fy, q]) => `Q${q} FY${String(fy % 100).padStart(2, '0')}`);
  const attach = qs.map(([fy, q]) => {
    const end = Math.min(qBounds(fy, q)[1], AS_OF);
    return sc.accs.length ? sc.accs.filter(a => a.fd != null && a.fd <= end).length / sc.accs.length : 0;
  });
  const fy25 = sum(M.won.filter(o => o.fq.fy === 2025), o => o.m);
  const growth = fy25 > 0 ? M.fy26b / fy25 - 1 : null;
  const fy26exp = sum(M.won.filter(o => o.t === 1 && o.fq.fy === 2026), o => o.m);
  body.innerHTML = `
  <div class="grid">${panel('rt-book', 'SASE bookings by quarter', `Closed-won land and expansion ARR. FY26 bookings were ${fmt.money(M.fy26b)}${growth != null ? `, ${growth >= 0 ? 'up' : 'down'} ${fmt.pct(Math.abs(growth), 0)} on FY25` : ''}. Q1 FY27 is quarter to date.`,
    legend([{ label: 'Land (first purchase)', color: PAL.ultra }, { label: 'Expansion', color: PAL.ultraSoft }]))}</div>
  <div class="grid">${panel('rt-attach', 'Attach rate at quarter end', 'Share of accounts in scope running Prisma Access')}</div>
  <aside class="action"><h3>What I would do</h3><ul><li>${esc(`Expansion was ${fmt.pct(M.fy26b ? fy26exp / M.fy26b : 0, 0)} of FY26 bookings. SD-WAN add-ons for existing Prisma Access customers are the cheapest growth in the book: no competitor, shorter cycles, higher win rates.`)}</li></ul></aside>`;
  chart('rt-book', el => Charts.vbar(el, labels, [
    { name: 'Land', values: land, color: PAL.ultra, tips: labels.map((l, i) => `${l}\nLand ${fmt.money(land[i])}\nExpansion ${fmt.money(exp[i])}\nTotal ${fmt.money(land[i] + exp[i])}`) },
    { name: 'Expansion', values: exp, color: PAL.ultraSoft, tips: labels.map((l, i) => `${l}\nLand ${fmt.money(land[i])}\nExpansion ${fmt.money(exp[i])}\nTotal ${fmt.money(land[i] + exp[i])}`) },
  ], { stacked: true, fmt: v => fmt.money(v), h: 260, aria: 'SASE bookings by quarter' }));
  chart('rt-attach', el => Charts.line(el, labels, [{ name: 'Attach', values: attach, color: PAL.ultra, dots: true }], { fmt: v => fmt.pct(v, 0), h: 220, aria: 'Attach rate at quarter end' }));
}
