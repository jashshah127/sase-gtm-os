/* Prisma Browser launch, Executive layer, and Operating cadence views. */
const KIT = [['icp', 'ICP'], ['positioning', 'Positioning'], ['battlecard', 'Battlecard'], ['discovery', 'Discovery guide'], ['scorecard', 'Scorecard']];

/* ================= Prisma Browser launch ================= */
function viewLaunch(root) {
  const icp = D.icp, L = D.launch;
  const tA = icp.tiers.find(t => t.tier === 'A'), tC = icp.tiers.find(t => t.tier === 'C');
  const ratio = tC.opps_per_100_accounts > 0 ? tA.opps_per_100_accounts / tC.opps_per_100_accounts : null;
  const wins = sum(icp.tiers, t => t.post_launch_wins);
  const liftRows = icp.table.filter(r => r.lift > 1).sort((a, b) => b.lift - a.lift).slice(0, 12);
  const weekLabels = L.weeks.map(w => { const [, m, d] = w.split('-').map(Number); return `${MONTHS[m - 1]} ${d}`; });
  const cum = arr => { let t = 0; return arr.map(v => (t += v)); };
  const line = name => L.lines.find(l => l.metric === name);
  const pov = line('POVs started'), japac = line('Field certified, JAPAC');
  const fmtLine = l => (l.metric === 'Pipeline created' ? fmt.money : l.metric.startsWith('Field') ? (v => fmt.pct(v, 0)) : fmt.int);

  root.innerHTML = `
  <header class="claim"><h1>Prisma Browser's first buyers look alike. Tier A accounts produced ${ratio ? ratio.toFixed(1) + 'x' : 'more of'} the post-launch pipeline of Tier C, account for account.</h1>
    <p class="lede">The ICP was built only from the ${icp.early_adopters} accounts that bought before the March 23, 2026 relaunch, then tested on the ${fmt.int(L.totals.opps)} deals created since. Tier A won ${tA.post_launch_wins} of ${wins} post-launch deals. The launch is close to plan on pipeline and wins; proof-of-value throughput is the constraint.</p></header>
  <div class="grid g2">
    ${panel('ln-lift', 'What early adopters have in common', 'Lift over the firewall base, by attribute. Points (12 x log2 of lift) feed the ICP score.')}
    <section class="panel"><h3>The ICP holds up out of time</h3><p class="cap">Tiers set from pre-relaunch adopters, then tested on deals created after March 23</p>
      ${table([
        { h: 'Tier', f: t => `<strong>${t.tier}</strong>` },
        { h: 'Accounts', num: true, f: t => fmt.int(t.accounts) },
        { h: 'Early adoption', num: true, f: t => fmt.pct(t.early_adopter_rate, 1) },
        { h: 'Opps per 100 accounts', num: true, f: t => t.opps_per_100_accounts.toFixed(1) },
        { h: 'Win rate', num: true, f: t => (t.post_launch_win_rate == null ? '–' : fmt.pct(t.post_launch_win_rate, 0)) },
      ], icp.tiers)}
      <p class="cap" style="margin-top:12px">Tier A is a score of ${icp.cutoffs.A} or more; Tier B is ${icp.cutoffs.B} or more. Opportunities and win rates are post-launch only.</p>
    </section>
  </div>

  <section class="block"><h2>Scorecard since relaunch</h2>
    ${table([
      { h: 'Metric', f: l => esc(l.metric) },
      { h: 'Actual', num: true, f: l => fmtLine(l)(l.actual) },
      { h: 'Plan to date', num: true, f: l => fmtLine(l)(l.plan) },
      { h: 'Attainment', num: true, f: l => fmt.pct(l.attainment, 0) },
      { h: 'Status', f: l => chip(l.status) },
    ], L.lines)}
    <div class="grid g3">
      ${panel('ln-pipe', 'Pipeline created', 'Cumulative against plan')}
      ${panel('ln-pov', 'POVs started', 'Cumulative against plan')}
      ${panel('ln-win', 'Deals won', 'Cumulative against plan')}
    </div>
    <div class="grid">${panel('ln-enable', 'Field certification by region', 'Share of sellers certified on the launch. The target path reaches 80% by week 12.',
      legend([{ label: 'AMER', color: PAL.ultra, kind: 'line' }, { label: 'EMEA', color: PAL.moss, kind: 'line' }, { label: 'JAPAC', color: PAL.crimson, kind: 'line' }, { label: 'Target path', color: PAL.ink, kind: 'dash' }]))}</div>
    <aside class="action"><h3>What I would do</h3><ul>
      <li>Add SE capacity or a packaged 30-day POV kit before adding top-of-funnel spend. POV starts are at ${fmt.pct(pov.attainment, 0)} of plan, and ${fmt.pct(L.totals.lost_at_pov_share, 0)} of losses happen at the POV stage.</li>
      <li>Run a JAPAC certification sprint with manager sign-off. JAPAC is at ${fmt.pct(japac.actual, 0)} against the 80% target.</li>
      <li>Route Tier A accounts to specialists first; Tier B goes to partner and marketing programs; Tier C stays in nurture.</li>
    </ul></aside>
  </section>

  <section class="block"><h2>Tier A target list</h2>
    <p class="serif narrow">Accounts that fit the profile and do not own Prisma Browser yet, with the entry point most likely to open the conversation.</p>
    <div class="filters" style="padding-top:4px">${selectHtml('ln-rg', 'Region', [[-1, 'All'], ...LK.regions.map((r, i) => [i, r])], S.launch.rg)}</div>
    <div id="ln-targets" style="margin-top:14px"></div>
  </section>

  <section class="block"><h2>Field kit</h2>
    <p class="serif narrow">Drafts a launch team would review with Product Marketing and Competitive Intelligence before field use. Capability statements stick to what Palo Alto Networks has announced publicly.</p>
    <div class="subtabs" role="group" aria-label="Field kit documents">${KIT.map(([id, name]) => `<button class="btn small" type="button" data-doc="${id}" aria-pressed="${S.launch.doc === id}">${name}</button>`).join('')}</div>
    <article class="panel doc" id="ln-doc"></article>
  </section>
  ${footer()}`;

  chart('ln-lift', el => Charts.hbar(el, liftRows.map(r => ({
    label: `${r.attribute}: ${r.value}`, value: r.lift, color: r.points >= 15 ? PAL.ultra : PAL.ultraMid,
    tip: `${r.attribute}: ${r.value}\n${fmt.pct(r.adopter_share)} of early adopters vs ${fmt.pct(r.base_share)} of the base\nLift ${r.lift.toFixed(2)}x, ${r.points} points`,
  })), { fmt: v => `${v.toFixed(1)}x`, labelW: 250, rowH: 26, ref: 1, refLabel: 'Base rate', aria: 'Early adopter lift by attribute' }));
  const small = (id, key, f) => chart(id, el => Charts.line(el, weekLabels, [
    { name: 'Plan', values: cum(L.plan[key]), color: PAL.slate, dashed: true, width: 1.8 },
    { name: 'Actual', values: cum(L.actual[key]), color: PAL.ultra, width: 2.4 },
  ], { fmt: f, h: 200, labelEvery: 9, aria: id }));
  small('ln-pipe', 'pipeline', v => fmt.money(v));
  small('ln-pov', 'povs', v => fmt.int(v));
  small('ln-win', 'wins', v => fmt.int(v));
  chart('ln-enable', el => Charts.line(el, weekLabels, [
    { name: 'AMER', values: L.enablement.AMER, color: PAL.ultra },
    { name: 'EMEA', values: L.enablement.EMEA, color: PAL.moss },
    { name: 'JAPAC', values: L.enablement.JAPAC, color: PAL.crimson },
    { name: 'Target path', values: L.enablement_plan, color: PAL.ink, dashed: true, width: 1.6 },
  ], { fmt: v => fmt.pct(v, 0), max: 1, h: 240, aria: 'Field certification by region' }));

  $('#ln-rg').addEventListener('change', e => { S.launch.rg = parseInt(e.target.value, 10); renderTargets(); });
  $$('[data-doc]').forEach(b => b.addEventListener('click', () => {
    S.launch.doc = b.dataset.doc;
    $$('[data-doc]').forEach(x => x.setAttribute('aria-pressed', String(x === b)));
    renderDoc();
  }));
  renderTargets();
  renderDoc();
}

function entryPoint(a) {
  if (a.vd && a.cn >= 15) return 'Retire VDI for contractors';
  if (a.um >= 30) return 'Secure unmanaged devices';
  if (a.pa) return 'Extend Prisma Access policy into the browser';
  return 'Govern AI use in the browser';
}

function renderTargets() {
  const rg = S.launch.rg;
  const list = ACC.filter(a => a.tier === 'A' && !a.bw && (rg < 0 || a.rg === rg))
    .map(a => ({ a, pot: Math.round((a.em * (a.cn / 100 + (0.5 * a.um) / 100) * D.cfg.browserPrice) / 100) * 100 }))
    .sort((x, y) => y.a.is - x.a.is || y.pot - x.pot);
  $('#ln-targets').innerHTML = `<p class="cap">${fmt.int(list.length)} Tier A accounts without Prisma Browser${rg >= 0 ? ' in ' + LK.regions[rg] : ''}. Top 20 by ICP score, then estimated Browser ARR.</p>` + table([
    { h: 'Account', f: x => `${esc(x.a.nm)}<span class="sub">${esc(LK.industries[x.a.in])}</span>` },
    { h: 'Segment', f: x => esc(LK.segments[x.a.sg]) },
    { h: 'Region', f: x => esc(LK.regions[x.a.rg]) },
    { h: 'Contractors', num: true, f: x => `${x.a.cn}%` },
    { h: 'Unmanaged devices', num: true, f: x => `${x.a.um}%` },
    { h: 'VDI', f: x => (x.a.vd ? 'Yes' : 'No') },
    { h: 'Prisma Access', f: x => (x.a.pa ? 'Customer' : 'No') },
    { h: 'ICP score', num: true, f: x => String(x.a.is) },
    { h: 'Est. Browser ARR', num: true, f: x => fmt.money(x.pot) },
    { h: 'Entry point', f: x => esc(entryPoint(x.a)) },
  ], list.slice(0, 20));
}

function renderDoc() { $('#ln-doc').innerHTML = D.docs[S.launch.doc] || ''; }

/* ================= Executive layer: the weekly business review drafts itself ================= */
function wbrWeeks() { const out = []; for (let d = Q1S + 6; d <= AS_OF; d += 7) out.push(d); return out; }

function buildWbr(weekEnd, rg) {
  const core = OPP.filter(o => o.core && (rg < 0 || o.acc.rg === rg));
  const ws = weekEnd - 6, [q2s, q2e] = qBounds(2027, 2);
  const fy26 = sum(core.filter(o => o.won && o.fq.fy === 2026), o => o.m);
  const target = fy26 * (1 + D.cfg.growth), q1Plan = target * D.cfg.seasonality[0], q2Plan = target * D.cfg.seasonality[1];
  const qtd = sum(core.filter(o => o.won && o.l >= Q1S && o.l <= weekEnd), o => o.m);
  const elapsed = (weekEnd - Q1S + 1) / (Q1E - Q1S + 1);
  const pacing = q1Plan > 0 ? qtd / (q1Plan * elapsed) : null;
  const inWeek = o => o.l >= ws && o.l <= weekEnd;
  const wins = core.filter(o => o.won && inWeek(o)).sort((a, b) => b.m - a.m);
  const losses = core.filter(o => o.lost && inWeek(o)).sort((a, b) => b.m - a.m);
  const created = k => createdInWeek(core, weekEnd - 7 * k);
  const cur = created(0), trail = [1, 2, 3, 4, 5, 6, 7, 8].map(created), avg = mean(trail), sd = stdev(trail);
  const z = sd > 0 ? (cur - avg) / sd : 0;
  const openAt = o => o.c <= weekEnd && (o.open || o.l > weekEnd);
  const q1Open = core.filter(o => openAt(o) && o.l >= Q1S && o.l <= Q1E);
  const q1Need = Math.max(0, q1Plan - qtd), q1Pipe = sum(q1Open, o => o.m);
  const q2Pipe = sum(core.filter(o => openAt(o) && o.l >= q2s && o.l <= q2e), o => o.m);
  const q2Cov = q2Plan > 0 ? q2Pipe / q2Plan : null;
  const slips = core.filter(o => o.q != null && o.q >= ws && o.q <= weekEnd);
  const repeat = slips.filter(o => o.u >= 2);
  const current = weekEnd === AS_OF;
  const risks = q1Open.filter(o => o.u >= 2 || (current && o.open && o.s === 2 && AS_OF - o.e > D.cfg.stageSla[2]))
    .sort((a, b) => b.m - a.m).slice(0, 3);
  const pastDue = current ? core.filter(o => o.open && o.l < AS_OF).length : 0;
  const weekNo = Math.floor((weekEnd - Q1S) / 7) + 1;

  const pace = pacing == null ? 'Q1 has no plan in this scope'
    : pacing >= 1.05 ? `Q1 is ahead of pace at ${fmt.pct(pacing, 0)} of plan`
    : pacing >= 0.95 ? `Q1 is on pace at ${fmt.pct(pacing, 0)} of plan`
    : `Q1 is behind pace at ${fmt.pct(pacing, 0)} of plan`;
  let risk = '';
  if (q2Cov != null && q2Cov < 1) risk = `Q2 pipeline covers only ${fmt.x(q2Cov)} of plan`;
  else if (z < -1.5) risk = 'pipeline creation fell well below trend';
  else if (repeat.length >= 3) risk = `${repeat.length} deals slipped for the second time or more`;
  const good = pacing != null && pacing >= 0.95;
  const headline = `${pace}${risk ? (good ? ', but ' : ', and ') + risk : ''}.`;

  const asks = [];
  if (q2Cov != null && q2Cov < 1.5) asks.push(`Marketing and Partners: a Q2 pipeline sprint. Q2 needs about ${fmt.money(Math.max(0, 1.5 * q2Plan - q2Pipe))} more pipeline to reach 1.5x coverage; prioritize mid-market and commercial deals that can close inside the quarter.`);
  if (z < -1.5) asks.push(`Regional sales leaders: explain the drop in pipeline creation, ${fmt.money(avg - cur)} below the 8-week average, by Monday. Seasonality, event timing, or a real slowdown?`);
  if (pacing != null && pacing < 0.95) asks.push(`Regional VPs: name two or three Q1 deals to pull forward. Q1 still needs ${fmt.money(q1Need)}, with ${fmt.x(q1Need > 0 ? q1Pipe / q1Need : null)} coverage.`);
  if (repeat.length) asks.push(`Deal owners: updated close plans for the ${repeat.length} repeat slippers (${fmt.money(sum(repeat, o => o.m))}) before Tuesday's forecast call.`);
  if (pastDue) asks.push(`Sales Ops: clear ${pastDue} past-due close dates before the forecast snapshot.`);
  return { weekEnd, weekNo, headline, qtd, q1Plan, pacing, q1Need, q1Pipe, q1Cov: q1Need > 0 ? q1Pipe / q1Need : null,
    q2Pipe, q2Plan, q2Cov, cur, avg, z, wins, losses, slips, repeat, risks, pastDue, asks, current,
    weekBookings: sum(wins, o => o.m) };
}

function wbrContent(w, rg) {
  const subj = `SASE WBR${rg < 0 ? '' : ' (' + LK.regions[rg] + ')'}, week ${w.weekNo} of FY27 Q1: ${w.headline}`;
  const deal = o => `${o.acc.nm} (${LK.segments[o.acc.sg]}, ${LK.regions[o.acc.rg]}), ${fmt.money(o.m)}, ${LK.products[o.p]}`;
  const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
  const sections = [
    ['Numbers', [
      `Bookings this week: ${fmt.money(w.weekBookings)} across ${plural(w.wins.length, 'deal')}. Quarter to date: ${fmt.money(w.qtd)}, ${w.pacing == null ? 'no plan in scope' : fmt.pct(w.pacing, 0) + ' of straight-line plan'} (Q1 plan ${fmt.money(w.q1Plan)}).`,
      `Pipeline created this week: ${fmt.money(w.cur)}, against an 8-week average of ${fmt.money(w.avg)} (${w.z >= 0 ? '+' : '−'}${Math.abs(w.z).toFixed(1)} standard deviations).`,
      `Coverage: the rest of Q1 at ${w.q1Cov == null ? 'plan already met' : fmt.x(w.q1Cov)} of what is still needed; Q2 at ${fmt.x(w.q2Cov)} of plan.`,
    ]],
    ['What moved', [
      ...w.wins.slice(0, 3).map(o => `Won: ${deal(o)}.`),
      ...w.losses.slice(0, 2).map(o => `Lost${o.k < 5 ? ' to ' + LK.competitors[o.k] : ''}: ${deal(o)}. Reason: ${(LK.lossReasons[o.r] || 'not recorded').toLowerCase()}.`),
      `Slipped: ${plural(w.slips.length, 'deal')} (${fmt.money(sum(w.slips, o => o.m))})${w.repeat.length ? `, ${w.repeat.length} of them for the second time or more` : ''}.`,
    ]],
    ['Risks', w.risks.length
      ? w.risks.map(o => `${o.acc.nm}: ${fmt.money(o.m)}, closing ${fmtDate(o.l, false)}, pushed ${plural(o.u, 'time')}${w.current && o.open ? `, in ${LK.stages[o.s]} for ${AS_OF - o.e} days` : ''}.`)
      : ['No flagged deals closing this quarter.']],
    ['Asks', w.asks.length ? w.asks : ['None this week.']],
  ];
  if (w.current) sections.push(['Hygiene', [`${plural(w.pastDue, 'open deal')} ${w.pastDue === 1 ? 'has' : 'have'} a past-due close date.`]]);
  const html = `<p class="subject">${esc(subj)}</p>` + sections.map(([h, items]) => `<h4>${esc(h)}</h4><ul>${items.map(i => `<li>${esc(i)}</li>`).join('')}</ul>`).join('');
  const text = `Subject: ${subj}\n\n` + sections.map(([h, items]) => `${h}\n${items.map(i => `- ${i}`).join('\n')}`).join('\n\n') + '\n';
  return { html, text };
}

function memoHtml(m) {
  return `<article class="memo"><h3 class="memo-title">${esc(m.subject)}</h3>
    <dl class="memo-meta"><dt>To</dt><dd>${esc(m.to)}</dd><dt>From</dt><dd>${esc(m.from)}</dd><dt>Date</dt><dd>${esc(m.date)}</dd></dl>
    <div class="bl"><strong>Bottom line.</strong> ${esc(m.bottom_line)}</div>
    ${m.sections.map(sec => `<h4>${esc(sec.title)}</h4>${sec.paragraph ? `<p>${esc(sec.paragraph)}</p>` : ''}${sec.bullets ? `<ul>${sec.bullets.map(([l, t]) => `<li><strong>${esc(l)}</strong> ${esc(t)}</li>`).join('')}</ul>` : ''}`).join('')}
    <p class="method">${esc(m.method)}</p></article>`;
}

function viewExec(root) {
  const weeks = wbrWeeks();
  if (!weeks.includes(S.wbr.week)) S.wbr.week = weeks[weeks.length - 1];
  root.innerHTML = `
  <header class="claim"><h1 id="wbr-claim"></h1>
    <p class="lede">Every Friday, the weekly business review drafts itself from the pipeline: what moved, what is at risk, and what I need from whom. An analyst edits the draft; it never replaces judgment.</p></header>
  <div class="filters">
    ${selectHtml('wbr-week', 'Week ending', weeks.map(d => [d, `Week ${Math.floor((d - Q1S) / 7) + 1}, ${fmtDate(d, false)}`]), S.wbr.week)}
    ${selectHtml('wbr-rg', 'Region', [[-1, 'All regions'], ...LK.regions.map((r, i) => [i, r])], S.wbr.rg)}
  </div>
  <div class="wbr-grid">
    <article class="panel wbr" id="wbr" aria-live="polite"></article>
    <aside class="panel side">
      <h3>This week at a glance</h3>
      <div id="wbr-side"></div>
      <div class="ctl-actions"><button class="btn primary" id="wbr-copy" type="button">Copy as text</button><span id="wbr-copied" class="muted" role="status" style="align-self:center"></span></div>
      <p class="cap" style="margin-top:12px">Earlier weeks are rebuilt from today's records, so a deal that slipped later shows its current close date.</p>
    </aside>
  </div>
  <section class="block"><h2>The one-page memo</h2>
    <p class="serif narrow">The flagship readout for a VP: the answer first, the evidence second, the asks third. Every number comes from the same data as this app. <a href="docs/executive_memo.pdf">Download the PDF</a>.</p>
    ${memoHtml(D.memo)}
  </section>
  ${footer()}`;
  $('#wbr-week').addEventListener('change', e => { S.wbr.week = parseInt(e.target.value, 10); renderWbr(); });
  $('#wbr-rg').addEventListener('change', e => { S.wbr.rg = parseInt(e.target.value, 10); renderWbr(); });
  $('#wbr-copy').addEventListener('click', () => {
    const text = $('#wbr').dataset.text || '';
    const done = ok => { $('#wbr-copied').textContent = ok ? 'Copied' : 'Select the text to copy'; };
    const fallback = () => {
      const ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      let ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      ta.remove(); done(ok);
    };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(() => done(true), fallback);
    else fallback();
  });
  renderWbr();
}

function renderWbr() {
  const w = buildWbr(S.wbr.week, S.wbr.rg), out = wbrContent(w, S.wbr.rg);
  $('#wbr-claim').textContent = `Week ${w.weekNo}: ${w.headline}`;
  const box = $('#wbr');
  box.innerHTML = out.html;
  box.dataset.text = out.text;
  $('#wbr-copied').textContent = '';
  $('#wbr-side').innerHTML = `<dl class="dl">
    <div><dt>Bookings this week</dt><dd>${fmt.money(w.weekBookings)}</dd></div>
    <div><dt>Quarter to date</dt><dd>${fmt.money(w.qtd)}</dd></div>
    <div><dt>Pacing to plan</dt><dd>${fmt.pct(w.pacing, 0)}</dd></div>
    <div><dt>Pipeline created</dt><dd>${fmt.money(w.cur)} <span class="muted">(${w.z >= 0 ? '+' : '−'}${Math.abs(w.z).toFixed(1)} SD)</span></dd></div>
    <div><dt>Q2 coverage</dt><dd>${fmt.x(w.q2Cov)}</dd></div>
    <div><dt>Deals slipped</dt><dd>${w.slips.length}</dd></div>
  </dl>`;
}

/* ================= Operating cadence ================= */
function viewCadence(root) {
  const CT = D.content, Q = D.quality;
  root.innerHTML = `
  <header class="claim"><h1>Numbers people trust come from shared definitions, a fixed rhythm, and checks that run before anyone sees a chart.</h1>
    <p class="lede">This is the operating layer: one dictionary that every chart and query uses, a weekly-to-annual rhythm aligned to the August fiscal year, clear ownership, and a data-quality gate that quarantined ${Q.quarantined_opportunities} bad records before they reached a metric.</p></header>
  <section><h2>Metric dictionary</h2>
    <div class="filters" style="padding-top:0"><label class="field" for="md-q">Search metrics<input type="search" id="md-q" placeholder="For example: coverage, win rate, ICP" value="${esc(S.cadence.q)}"></label></div>
    <div id="md-table" style="margin-top:12px"></div>
  </section>
  <section class="block"><h2>Operating rhythm</h2>
    <div class="grid g3 rhythm">${CT.rhythm.map(b => `<section class="panel"><h3>${esc(b.cadence)}</h3><ul>${b.items.map(([when, what, who]) => `<li><b>${esc(when)}</b>${esc(what)}<small>${esc(who)}</small></li>`).join('')}</ul></section>`).join('')}</div>
  </section>
  <section class="block"><h2>FY28 planning calendar</h2>
    <p class="serif narrow">The fiscal year starts August 1, so planning for FY28 runs February through July 2027.</p>
    <div class="timeline">${CT.calendar.map(([mo, what, who]) => `<div><b>${esc(mo)}</b><span>${esc(what)}</span><small>${esc(who)}</small></div>`).join('')}</div>
  </section>
  <section class="block"><h2>Who owns what</h2>
    <p class="cap">R responsible, A accountable (exactly one per row), C consulted, I informed</p>
    ${table([
      { h: 'Activity', f: r => esc(r[0]) },
      ...CT.functions.map((fn, j) => ({ h: fn === 'GTM Strategy' ? 'GTM Strategy (this role)' : fn, f: r => (r[j + 1] ? `<span class="rc rc-${r[j + 1]}">${r[j + 1]}</span>` : '<span class="muted">–</span>') })),
    ], CT.raci, { cls: 'raci' })}
  </section>
  <section class="block"><h2>Data-quality gate</h2>
    <p class="serif narrow">Known issues are injected into the raw export on purpose, and the build fails unless every one is caught. ${fmt.int(Q.raw_opportunities)} raw opportunities in, ${fmt.int(Q.clean_opportunities)} clean ones out; ${Q.raw_accounts - Q.clean_accounts} duplicate accounts merged.</p>
    ${table([
      { h: 'Check', f: c => `${esc(c.check)}<span class="sub">${esc(c.description)}</span>` },
      { h: 'Rows checked', num: true, f: c => fmt.int(c.rows_checked) },
      { h: 'Failed', num: true, f: c => fmt.int(c.rows_failed) },
      { h: 'Action', f: c => chip(c.action) },
      { h: 'Owner', f: c => esc(c.owner) },
    ], Q.checks)}
  </section>
  <section class="block"><h2>Mentoring: analyst onboarding</h2><article class="panel doc">${D.docs.onboarding}</article></section>
  ${footer()}`;
  const render = () => {
    const q = S.cadence.q.trim().toLowerCase();
    const rows = CT.metrics.filter(m => !q || Object.values(m).some(v => String(v).toLowerCase().includes(q)));
    $('#md-table').innerHTML = rows.length ? table([
      { h: 'Metric', f: m => `<strong>${esc(m.metric)}</strong>` },
      { h: 'Definition', f: m => `${esc(m.definition)}<span class="sub">Watch out: ${esc(m.caveat)}</span>` },
      { h: 'Formula', f: m => esc(m.formula) },
      { h: 'Owner', f: m => esc(m.owner) },
      { h: 'Cadence', f: m => esc(m.cadence) },
    ], rows) : `<p class="empty">No metric matches "${esc(S.cadence.q)}". Try a shorter term.</p>`;
  };
  $('#md-q').addEventListener('input', e => { S.cadence.q = e.target.value; render(); });
  render();
}
