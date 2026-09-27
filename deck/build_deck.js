/*
 * SASE GTM readout deck. Every number comes from deck/deck_data.json (built from the pipeline),
 * so the deck always matches the app and the memo.
 *   python deck/deck_data.py && node deck/build_deck.js [output.pptx]
 */
const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const sharp = require('sharp');
const Fi = require('react-icons/fi');

const D = JSON.parse(fs.readFileSync(path.join(__dirname, 'deck_data.json'), 'utf8'));
const OUT = process.argv[2] || path.join(__dirname, '..', 'docs', 'SASE_GTM_readout.pptx');

const C = {
  ink: '0F1B33', ink2: '3A4760', ultra: '2B3FE0', ultraMid: '7B88EC', ultraSoft: 'E7EAFD', ultraPale: 'C4CAF6',
  moss: '2E7D5B', mossSoft: 'E1F0E8', crimson: 'C23B4E', crimsonSoft: 'F8E3E6', amber: '8A5A08', amberSoft: 'FAEFD9',
  slate: '8290A6', slate2: '56657E', slateSoft: 'C3CBD8', haze: 'DCE2EC', chalk: 'F2F4F7', white: 'FFFFFF', night: '233050',
};
const F = { head: 'Arial', body: 'Calibri', serif: 'Cambria' };
const W = 13.333, X0 = 0.6, CW = W - 2 * X0;
const SYNTH = 'Synthetic data: a 4,200-account model book calibrated to public figures. Method and sources in the appendix.';

const money = (v, d = 1) => (Math.abs(v) >= 1e6 ? `$${(v / 1e6).toFixed(d)}M` : `$${Math.round(v / 1e3)}K`);
const pct = (v, d = 0) => `${(v * 100).toFixed(d)}%`;
const times = v => `${v.toFixed(2)}x`;
const int = v => Math.round(v).toLocaleString('en-US');

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.author = D.author;
pres.title = 'Closing the FY27 SASE gap';
pres.subject = 'SASE Product GTM readout (independent portfolio exercise)';
pres.theme = { headFontFace: F.head, bodyFontFace: F.body };

/* Typography applied to every text box and table: curly apostrophes, and non-breaking hyphens so
   terms like SD-WAN never split across lines. */
function typo(t) {
  if (typeof t !== 'string' || /:\/\/|\.(com|io|org)\b/.test(t)) return t;   // never touch links
  return t.replace(/([A-Za-z])'([A-Za-z])/g, '$1\u2019$2').replace(/([A-Za-z])-([A-Za-z])/g, '$1\u2011$2');
}
const typoRuns = t => (Array.isArray(t) ? t.map(r => ({ ...r, text: typo(r.text) })) : typo(t));
const rawAddSlide = pres.addSlide.bind(pres);
pres.addSlide = (...args) => {
  const sl = rawAddSlide(...args);
  const addText = sl.addText.bind(sl), addTable = sl.addTable.bind(sl);
  sl.addText = (text, opts) => addText(typoRuns(text), opts);
  sl.addTable = (rows, opts) => addTable(rows.map(r => r.map(c => (typeof c === 'string' ? typo(c) : { ...c, text: typo(c.text) }))), opts);
  return sl;
};

async function iconData(Comp, hex) {
  const svg = renderToStaticMarkup(React.createElement(Comp, { size: 256, color: `#${hex}` })).replace(/currentColor/g, `#${hex}`);
  const buf = await sharp(Buffer.from(svg)).resize(256, 256).png().toBuffer();
  return `image/png;base64,${buf.toString('base64')}`;
}

/* ---------- building blocks ---------- */
function header(slide, label, title, dark = false, size = 26) {
  slide.addText(label, { x: X0, y: 0.42, w: 9, h: 0.3, fontFace: F.body, fontSize: 12, bold: true, color: dark ? C.ultraPale : C.ultra, margin: 0, isTextBox: true });
  slide.addText(title, { x: X0, y: 0.76, w: CW, h: 1.1, fontFace: F.head, fontSize: size, bold: true, color: dark ? C.white : C.ink, valign: 'top', margin: 0, isTextBox: true });
}
function footer(slide, note, n, dark = false) {
  const color = dark ? C.slate : C.slate2;
  slide.addText(note, { x: X0, y: 7.0, w: CW - 0.8, h: 0.3, fontFace: F.body, fontSize: 10, color, margin: 0, isTextBox: true, valign: 'middle' });
  slide.addText(String(n), { x: W - X0 - 0.5, y: 7.0, w: 0.5, h: 0.3, fontFace: F.body, fontSize: 10, color, align: 'right', margin: 0, isTextBox: true, valign: 'middle' });
}
function soWhat(slide, text) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: X0, y: 6.05, w: CW, h: 0.72, fill: { color: C.ultraSoft }, line: { color: C.ultraSoft }, rectRadius: 0.1 });
  slide.addText([
    { text: 'So what   ', options: { bold: true, color: C.ultra } },
    { text, options: { color: C.ink } },
  ], { x: X0 + 0.28, y: 6.05, w: CW - 0.56, h: 0.72, fontFace: F.body, fontSize: 15, valign: 'middle', margin: 0, isTextBox: true });
}
function panelTitle(slide, x, y, w, title, note) {
  slide.addText(title, { x, y, w, h: 0.32, fontFace: F.body, fontSize: 15, bold: true, color: C.ink, margin: 0, isTextBox: true, valign: 'top' });
  if (note) slide.addText(note, { x, y: y + 0.34, w, h: 0.3, fontFace: F.body, fontSize: 11, color: C.slate2, margin: 0, isTextBox: true, valign: 'top' });
}
function stat(slide, { x, y, w, big, label, color = C.ultra, size = 40, bigH = 0.66, labelH = 0.52, labelSize = 13 }) {
  slide.addText(big, { x, y, w, h: bigH, fontFace: F.head, fontSize: size, bold: true, color, margin: 0, isTextBox: true, valign: 'bottom' });
  slide.addText(label, { x, y: y + bigH + 0.06, w, h: labelH, fontFace: F.body, fontSize: labelSize, color: C.ink2, margin: 0, isTextBox: true, valign: 'top' });
}
function pill(slide, text, fill, color, x, y, w) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.36, fill: { color: fill }, line: { color: fill }, rectRadius: 0.18 });
  slide.addText(text, { x, y, w, h: 0.36, fontFace: F.body, fontSize: 11, bold: true, color, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
}
/* One series per color with zeros elsewhere; with 100% overlap each bar keeps its own color. */
function colorSeries(labels, values, colorOf) {
  const groups = [];
  values.forEach((v, i) => {
    const c = colorOf(i);
    let g = groups.find(x => x.color === c);
    if (!g) { g = { color: c, values: labels.map(() => 0) }; groups.push(g); }
    g.values[i] = v;
  });
  const lab = labels.map(typo);
  return { data: groups.map((g, k) => ({ name: `Series ${k + 1}`, labels: lab, values: g.values })), colors: groups.map(g => g.color) };
}
function chartOpts(extra) {
  return Object.assign({
    showLegend: false, showTitle: false,
    catAxisLabelColor: C.ink2, catAxisLabelFontFace: F.body, catAxisLabelFontSize: 12, catAxisLineShow: false,
    valAxisHidden: true, valAxisLineShow: false, valGridLine: { style: 'none' }, catGridLine: { style: 'none' },
    showValue: true, dataLabelPosition: 'outEnd', dataLabelFontFace: F.body, dataLabelFontSize: 12,
    dataLabelFontBold: true, dataLabelColor: C.ink, barGapWidthPct: 60,
  }, extra);
}
const cell = (text, o = {}) => ({ text, options: Object.assign({ fontFace: F.body, fontSize: 12, color: C.ink, valign: 'middle',
  border: [{ type: 'none' }, { type: 'none' }, { type: 'solid', pt: 0.75, color: C.haze }, { type: 'none' }] }, o) });
const headCell = (text, o = {}) => cell(text, Object.assign({ bold: true, color: C.slate2, fontSize: 11,
  border: [{ type: 'none' }, { type: 'none' }, { type: 'solid', pt: 1, color: C.ink }, { type: 'none' }] }, o));
function card(slide, x, y, w, h, title, body, value) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: C.chalk }, line: { color: C.chalk }, rectRadius: 0.1 });
  slide.addText(title, { x: x + 0.22, y: y + 0.16, w: w - 0.44, h: 0.3, fontFace: F.body, fontSize: 15, bold: true, color: C.ink, margin: 0, isTextBox: true });
  slide.addText(body, { x: x + 0.22, y: y + 0.5, w: w - 0.44, h: 0.3, fontFace: F.body, fontSize: 12, color: C.ink2, margin: 0, isTextBox: true });
  slide.addText(value, { x: x + 0.22, y: y + 0.86, w: w - 0.44, h: 0.55, fontFace: F.head, fontSize: 28, bold: true, color: C.ultra, margin: 0, isTextBox: true, valign: 'middle' });
}
async function iconRow(slide, Icon, x, y, title, body, bodyW) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: 0.62, h: 0.62, fill: { color: C.ultra }, line: { color: C.ultra } });
  slide.addImage({ data: await iconData(Icon, C.white), x: x + 0.15, y: y + 0.15, w: 0.32, h: 0.32 });
  slide.addText(title, { x: x + 0.85, y: y - 0.02, w: bodyW, h: 0.34, fontFace: F.body, fontSize: 15, bold: true, color: C.ink, margin: 0, isTextBox: true });
  slide.addText(body, { x: x + 0.85, y: y + 0.34, w: bodyW, h: 0.68, fontFace: F.body, fontSize: 13, color: C.ink2, margin: 0, isTextBox: true, valign: 'top' });
}

async function build() {
  const unc = D.unc, cov = D.cov, lev = D.levers, deal = D.deal;
  const rec = D.scenarios.find(s => s.name.startsWith('Recommended'));

  /* 1. Title */
  const s1 = pres.addSlide();
  s1.background = { color: C.ink };
  s1.addText('SASE Product GTM readout', { x: 0.8, y: 1.25, w: 7, h: 0.35, fontFace: F.body, fontSize: 14, bold: true, color: C.ultraPale, margin: 0, isTextBox: true });
  s1.addText('Closing the FY27 SASE gap', { x: 0.8, y: 1.7, w: 7.3, h: 1.75, fontFace: F.head, fontSize: 50, bold: true, color: C.white, margin: 0, isTextBox: true, valign: 'top' });
  s1.addText('Coverage, timing, and the SD-WAN bundle', { x: 0.8, y: 3.55, w: 7.3, h: 0.5, fontFace: F.serif, fontSize: 24, italic: true, color: C.haze, margin: 0, isTextBox: true });
  s1.addText('A working model of the SASE Product GTM Manager role', { x: 0.8, y: 4.22, w: 7.3, h: 0.35, fontFace: F.body, fontSize: 16, color: C.slateSoft, margin: 0, isTextBox: true });
  s1.addText([{ text: D.author, options: { bold: true, color: C.white, breakLine: true } }, { text: 'September 2026', options: { color: C.slateSoft } }],
    { x: 0.8, y: 5.0, w: 5, h: 0.7, fontFace: F.body, fontSize: 16, margin: 0, isTextBox: true, valign: 'top' });
  s1.addText('Synthetic deals, real market. An independent exercise, not affiliated with or endorsed by Palo Alto Networks.',
    { x: 0.8, y: 6.72, w: 11.5, h: 0.3, fontFace: F.body, fontSize: 11, color: C.slate, margin: 0, isTextBox: true });
  // Motif: each dot is an account. Filled dots run Prisma Access; outlined dots are customers the model expects but coverage misses.
  let seed = 7;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const cols = 12, rows = 11, step = 0.36, dia = 0.2, gx = 8.55, gy = 1.3;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const u = rnd(), latentZone = r >= 6 && c >= 5;
    const kind = u < (latentZone ? 0.1 : 0.3) ? 'cust' : latentZone && u < 0.3 ? 'latent' : 'other';
    const o = { x: gx + c * step, y: gy + r * step, w: dia, h: dia };
    if (kind === 'cust') s1.addShape(pres.shapes.OVAL, { ...o, fill: { color: C.ultraMid }, line: { color: C.ultraMid } });
    else if (kind === 'latent') s1.addShape(pres.shapes.OVAL, { ...o, fill: { color: C.ink }, line: { color: C.ultraPale, width: 1.5 } });
    else s1.addShape(pres.shapes.OVAL, { ...o, fill: { color: C.night }, line: { color: C.night } });
  }
  s1.addShape(pres.shapes.OVAL, { x: 8.55, y: 5.42, w: 0.16, h: 0.16, fill: { color: C.ultraMid }, line: { color: C.ultraMid } });
  s1.addText('Prisma Access customer', { x: 8.8, y: 5.35, w: 1.9, h: 0.3, fontFace: F.body, fontSize: 11, color: C.slateSoft, margin: 0, isTextBox: true, valign: 'middle' });
  s1.addShape(pres.shapes.OVAL, { x: 10.7, y: 5.42, w: 0.16, h: 0.16, fill: { color: C.ink }, line: { color: C.ultraPale, width: 1.25 } });
  s1.addText('Expected, but uncovered', { x: 10.95, y: 5.35, w: 1.9, h: 0.3, fontFace: F.body, fontSize: 11, color: C.slateSoft, margin: 0, isTextBox: true, valign: 'middle' });
  s1.addNotes(`Open with the question, not the tool: "FY27 needs ${money(D.fy27_target)} of SASE bookings, 35% more than last year. I built a working model of this role to answer where it comes from." Say early that the deals are synthetic and calibrated to public figures, and that the market data is real. Then move on; the method is what matters. Each dot on the right is an account: filled dots run Prisma Access, outlined dots are customers the model expects but coverage misses. That picture is the whole story.`);

  /* 2. The answer */
  const s2 = pres.addSlide();
  header(s2, 'The answer', `FY27 is reachable with ${D.rec_hires} specialist hires, not ${D.hire_only}, by fixing coverage, timing, and the bundle.`);
  const findings = [
    [String(unc.latent_customers), `customers missing from territories with no SASE specialist, where attach is ${pct(unc.actual_attach, 1)} against a modeled ${pct(unc.modeled_attach, 1)}`, C.ultra],
    [pct(deal.adj_win_sse_bundle), `win rate against Zscaler and Netskope when SD-WAN is in the deal, versus ${pct(deal.adj_win_sse_no_bundle)} without it`, C.ultra],
    [times(D.coverage[1].coverage), `Q2 pipeline coverage. Q1 is pacing ${pct(D.q1_pacing)} of plan, so next quarter is the real risk`, C.crimson],
  ];
  findings.forEach(([big, text, color], i) => {
    const y = 2.1 + i * 1.25;
    s2.addText(big, { x: X0, y, w: 1.95, h: 0.8, fontFace: F.head, fontSize: 36, bold: true, color, margin: 0, isTextBox: true, valign: 'middle' });
    s2.addText(text, { x: X0 + 2.05, y, w: 3.95, h: 0.8, fontFace: F.body, fontSize: 14, color: C.ink, margin: 0, isTextBox: true, valign: 'middle' });
    if (i < 2) s2.addShape(pres.shapes.LINE, { x: X0, y: y + 1.02, w: 6.0, h: 0, line: { color: C.haze, width: 1 } });
  });
  panelTitle(s2, 7.1, 2.05, 5.6, 'Modeled FY27 attainment by option', `Share of the ${money(D.fy27_target)} bookings target`);
  const scenLabels = D.scenarios.map(x => (x.name.startsWith('Recommended') ? `Plays + ${x.hires} hires`
    : x.name === 'Hiring only' ? `Hiring only (${x.hires} hires)` : x.name === 'Win-rate plays' ? 'Two win-rate plays' : x.name));
  const sc2 = colorSeries(scenLabels, D.scenarios.map(x => x.attainment), i => (D.scenarios[i].attainment >= 1 ? C.moss : i === 0 ? C.slate : C.ultraMid));
  s2.addChart(pres.charts.BAR, sc2.data, chartOpts({ x: 6.95, y: 2.72, w: 5.8, h: 2.85, barDir: 'bar', barGrouping: 'clustered', barOverlapPct: 100,
    chartColors: sc2.colors, catAxisOrientation: 'maxMin', valAxisMinVal: 0, valAxisMaxVal: 1.18, dataLabelFormatCode: '0%;;;', barGapWidthPct: 45 }));
  s2.addText(`Hiring alone costs ${money(D.hire_only_cost)} in FY27; the recommended plan costs ${money(D.rec_cost)}.`,
    { x: 7.1, y: 5.58, w: 5.6, h: 0.3, fontFace: F.body, fontSize: 11.5, color: C.slate2, margin: 0, isTextBox: true });
  soWhat(s2, `The ask: approve ${D.rec_hires} specialists for JAPAC and EMEA mid-market, make SD-WAN the default in rival deals, time attach to firewall renewals, and run a Q2 pipeline sprint.`);
  footer(s2, SYNTH, 2);
  s2.addNotes(`This is the whole story on one slide. FY27 needs ${money(D.fy27_target)}; today's capacity reaches about ${pct(D.scenarios[0].attainment)}. Three findings drive the plan: ${unc.latent_customers} customers missing where we have no specialist; SD-WAN nearly doubling win rates against SSE-only rivals; and a thin Q2 pipeline even though Q1 is ahead. The punchline: hiring alone takes ${D.hire_only} specialists and ${money(D.hire_only_cost)}. Two process changes plus ${D.rec_hires} targeted hires get there for ${money(D.rec_cost)}. If time is short, present this slide, the plan (slide 8), and stop.`);

  /* 3. Market (real data) */
  const s3 = pres.addSlide();
  header(s3, 'Market context', "Palo Alto's SASE ARR is growing about twice as fast as the market, and the market is consolidating.");
  pill(s3, 'Real public data', C.mossSoft, C.moss, W - X0 - 1.8, 0.38, 1.8);
  panelTitle(s3, X0, 2.05, 7.0, 'Latest reported year-over-year growth', 'Most recent period each company reported. Definitions differ by company.');
  const g = [...D.market_growth].sort((a, b) => b.growth - a.growth);
  const shortMetric = m => (m === 'ARR excluding Red Canary' ? 'organic ARR' : m);
  const gLabels = g.map(x => (x.kind === 'market' ? `SASE market, Dell'Oro (${x.fiscal_period})` : `${x.company}: ${shortMetric(x.metric)} (${x.fiscal_period})`));
  const sc3 = colorSeries(gLabels, g.map(x => x.growth), i => (g[i].ticker === 'PANW' ? C.ultra : g[i].kind === 'market' ? C.ink : C.slateSoft));
  s3.addChart(pres.charts.BAR, sc3.data, chartOpts({ x: 0.45, y: 2.72, w: 7.2, h: 3.0, barDir: 'bar', barGrouping: 'clustered', barOverlapPct: 100,
    chartColors: sc3.colors, catAxisOrientation: 'maxMin', valAxisMinVal: 0, valAxisMaxVal: 0.5, dataLabelFormatCode: '0%;;;', catAxisLabelFontSize: 11.5, barGapWidthPct: 45 }));
  stat(s3, { x: 8.3, y: 2.05, w: 4.43, big: `$${D.forecast_2029}B`, label: "SASE market Dell'Oro forecasts for 2029", size: 38 });
  stat(s3, { x: 8.3, y: 3.3, w: 4.43, big: `${D.single_vendor}%`, label: 'of that market expected to go to single-vendor SASE', size: 38 });
  stat(s3, { x: 8.3, y: 4.55, w: 4.43, big: `${D.top_six}%`, label: 'held by the top six vendors in 2024, up from 64% in 2023', size: 38, color: C.slate2 });
  soWhat(s3, 'Single-vendor SASE is where the market is heading, so leading with SD-WAN is strategy, not just a win-rate tactic.');
  footer(s3, "Sources: company earnings releases and Dell'Oro Group press releases (appendix). ARR definitions differ, so compare direction, not decimals.", 3);
  s3.addNotes(`The one slide built entirely on public data. Palo Alto's SASE ARR grew 40% against 21% for the SASE market per Dell'Oro, so it's taking share. Dell'Oro expects single-vendor SASE to take ${D.single_vendor}% of a $${D.forecast_2029} billion market by 2029, which is why the SD-WAN bundle matters strategically, not just tactically. Say the caveat before anyone asks: Zscaler and Netskope report company-wide ARR, Palo Alto and Fortinet report SASE-specific ARR, and Dell'Oro measures revenue. Say "about twice," never a precise multiple.`);

  /* 4. Coverage */
  const s4 = pres.addSlide();
  header(s4, 'The opportunity', `The gap is coverage, not demand: uncovered territories attach at ${pct(unc.actual_attach)} against a modeled ${pct(unc.modeled_attach)}.`);
  panelTitle(s4, X0, 2.05, 6.2, 'Attach rate, actual versus modeled', 'The model is trained only where coverage is good, so it shows what attach should be.');
  s4.addChart(pres.charts.BAR, [
    { name: 'Actual attach', labels: ['With a SASE specialist', 'No SASE specialist'], values: [cov.actual_attach, unc.actual_attach] },
    { name: 'Modeled attach', labels: ['With a SASE specialist', 'No SASE specialist'], values: [cov.modeled_attach, unc.modeled_attach] },
  ], chartOpts({ x: 0.45, y: 2.72, w: 6.4, h: 3.05, barDir: 'col', barGrouping: 'clustered', chartColors: [C.ultra, C.slateSoft],
    valAxisMinVal: 0, valAxisMaxVal: 0.45, dataLabelFormatCode: '0%', showLegend: true, legendPos: 'b', legendFontFace: F.body,
    legendFontSize: 12, legendColor: C.ink2, barGapWidthPct: 80 }));
  stat(s4, { x: 7.35, y: 2.05, w: 2.55, big: String(unc.latent_customers), label: "customers the model expects but we don't have", size: 38 });
  stat(s4, { x: 10.15, y: 2.05, w: 2.58, big: `$${Math.round(D.whitespace / 1e6)}M`, label: `in whitespace, half of it in ${D.half_accounts} accounts`, size: 38 });
  s4.addText('Largest gaps: modeled minus actual attach', { x: 7.35, y: 3.62, w: 5.38, h: 0.3, fontFace: F.body, fontSize: 13, bold: true, color: C.ink, margin: 0, isTextBox: true });
  s4.addTable([
    [headCell('Region and segment'), headCell('Gap', { align: 'right' })],
    ...D.gaps.map(r => [cell(`${r.region} ${r.segment}`), cell(`${Math.round(r.gap_pts)} pts`, { align: 'right', bold: true })]),
  ], { x: 7.35, y: 4.0, w: 5.38, colW: [4.0, 1.38], rowH: 0.34 });
  soWhat(s4, 'Put specialist coverage where the model says demand already exists, and prove it with a staggered pilot before scaling.');
  footer(s4, SYNTH, 4);
  s4.addNotes(`Where a specialist covers the territory, actual attach matches the model: ${pct(cov.actual_attach, 1)}. Where none does, attach is ${pct(unc.actual_attach, 1)} against a modeled ${pct(unc.modeled_attach, 1)}: about ${unc.latent_customers} customers we'd expect and don't have, mostly JAPAC and EMEA mid-market and commercial. Key method point: the model was trained only on covered territories, so its score means "attach under good coverage." Half of the ${money(D.whitespace, 0)} propensity-weighted whitespace sits in just ${D.half_accounts} accounts. If asked "is it causal?": not from this data alone; covered territories may have been stronger. That's why slide 9 proposes a pilot.`);

  /* 5. Win rate */
  const s5 = pres.addSlide();
  header(s5, 'Win rate', `Two process changes add about ${D.plays_pts} points of win rate, worth ${money(D.plays_forecast - D.baseline_forecast)} in FY27, with no new headcount.`);
  panelTitle(s5, X0, 2.05, 3.9, 'Against Zscaler or Netskope', 'Win rate on closed land deals');
  const a5 = colorSeries(['Without SD-WAN', 'SD-WAN in the deal'], [deal.adj_win_sse_no_bundle, deal.adj_win_sse_bundle], i => (i ? C.ultra : C.slateSoft));
  s5.addChart(pres.charts.BAR, a5.data, chartOpts({ x: 0.45, y: 2.72, w: 4.1, h: 2.75, barDir: 'col', barGrouping: 'clustered', barOverlapPct: 100,
    chartColors: a5.colors, valAxisMinVal: 0, valAxisMaxVal: 0.6, dataLabelFormatCode: '0%;;;', dataLabelFontSize: 14, barGapWidthPct: 70 }));
  panelTitle(s5, 4.85, 2.05, 3.9, 'Timing against the firewall renewal', 'Win rate on closed land deals');
  const b5 = colorSeries(['Other timing', '90 to 270 days before'], [deal.adj_win_not_aligned, deal.adj_win_aligned], i => (i ? C.ultra : C.slateSoft));
  s5.addChart(pres.charts.BAR, b5.data, chartOpts({ x: 4.7, y: 2.72, w: 4.1, h: 2.75, barDir: 'col', barGrouping: 'clustered', barOverlapPct: 100,
    chartColors: b5.colors, valAxisMinVal: 0, valAxisMaxVal: 0.6, dataLabelFormatCode: '0%;;;', dataLabelFontSize: 14, barGapWidthPct: 70 }));
  s5.addText(`Adjusted for coverage, segment, timing, and source across ${int(D.closed_land_deals)} closed land deals.`,
    { x: X0, y: 5.5, w: 8.2, h: 0.3, fontFace: F.body, fontSize: 11, color: C.slate2, margin: 0, isTextBox: true });
  card(s5, 9.15, 2.05, 3.58, 1.6, 'SD-WAN in rival deals', `Today ${pct(lev.bundle_share_in_sse_now)} of those deals; target ${pct(lev.bundle_share_target)}`, `+${lev.bundle_pts} pts`);
  card(s5, 9.15, 3.85, 3.58, 1.6, 'Renewal-timed attach', `Today ${pct(lev.aligned_share_now)} of land deals; target ${pct(lev.aligned_share_target)}`, `+${lev.renewal_pts} pts`);
  soWhat(s5, 'Both are process changes, not budget asks, so they can start at the Q2 kickoff.');
  footer(s5, SYNTH, 5);
  s5.addNotes(`Against Zscaler and Netskope, deals that include SD-WAN win ${pct(deal.adj_win_sse_bundle)} versus ${pct(deal.adj_win_sse_no_bundle)}. Deals opened 90 to 270 days before the firewall renewal win ${pct(deal.adj_win_aligned)} versus ${pct(deal.adj_win_not_aligned)}. These are adjusted numbers from a logistic regression controlling for coverage, segment, timing, and source, because the sellers who bundle also tend to have better coverage. Sizing: moving the bundle rate in rival deals from ${pct(lev.bundle_share_in_sse_now)} to ${pct(lev.bundle_share_target)} is worth ${lev.bundle_pts} points of blended win rate; moving renewal-timed deals from ${pct(lev.aligned_share_now)} to ${pct(lev.aligned_share_target)} is worth ${lev.renewal_pts}. With real data I'd confirm the bundle effect with win/loss interviews before changing the playbook.`);

  /* 6. Pipeline */
  const s6 = pres.addSlide();
  header(s6, 'Pipeline', "Q1 is ahead of plan. Q2 is where FY27 slips if pipeline creation doesn't rise now.");
  stat(s6, { x: X0, y: 2.05, w: 4.7, big: pct(D.q1_pacing), label: `Q1 pacing to plan at week 8: ${money(D.q1_qtd)} booked against a ${money(D.q1_plan)} quarter`, color: C.moss, size: 44, bigH: 0.75, labelH: 0.62 });
  stat(s6, { x: X0, y: 3.75, w: 4.7, big: times(D.coverage[1].coverage), label: `Q2 coverage: ${money(D.coverage[1].pipeline)} of pipeline against a ${money(D.q2_plan)} plan, where about 2x is healthy`, color: C.crimson, size: 44, bigH: 0.75, labelH: 0.62 });
  panelTitle(s6, 5.85, 2.05, 6.9, 'Pipeline coverage by quarter', 'Open pipeline closing in the quarter, divided by plan still to book');
  const c6 = colorSeries(['Rest of Q1', 'Q2', 'Q3', 'Q4'], D.coverage.map(c => c.coverage || 0), i => (i === 0 ? C.moss : i === 1 ? C.crimson : C.slateSoft));
  s6.addChart(pres.charts.BAR, c6.data, chartOpts({ x: 5.7, y: 2.72, w: 7.1, h: 3.05, barDir: 'col', barGrouping: 'clustered', barOverlapPct: 100,
    chartColors: c6.colors, valAxisMinVal: 0, valAxisMaxVal: 3.7, dataLabelFormatCode: '0.00"x";;;', dataLabelFontSize: 13, barGapWidthPct: 60 }));
  soWhat(s6, `Q2 pipeline sprint: lift weekly creation from ${money(D.weekly_pipeline)} to ${money(D.weekly_pipeline + 1e6)} through mid-November, weighted to mid-market deals that can close in the quarter.`);
  footer(s6, SYNTH, 6);
  s6.addNotes(`Q1 looks fine: ${pct(D.q1_pacing)} of straight-line plan at week 8. The risk is next quarter: pipeline closing in Q2 covers only ${times(D.coverage[1].coverage)} of plan, where about 2x is healthy at this point. Q3 and Q4 look thin too, but that's normal this early; sellers create those deals later. The ask is concrete: raise weekly pipeline creation by about $1 million through mid-November, and weight it to mid-market and commercial deals, whose cycles are short enough to close inside Q2. This is the section the weekly business review in the app flags automatically.`);

  /* 7. Prisma Browser launch */
  const s7 = pres.addSlide();
  const T = D.tiers, winsAll = T.A.post_launch_wins + T.B.post_launch_wins + T.C.post_launch_wins;
  header(s7, 'Prisma Browser launch', "Prisma Browser's ICP works. Proof-of-value capacity, not demand, is the launch constraint.");
  panelTitle(s7, X0, 2.05, 6.0, 'Post-launch deals per 100 accounts, by ICP tier', 'Tiers built from pre-launch buyers only, then tested on deals created after March 23');
  const t7 = colorSeries(['Tier A', 'Tier B', 'Tier C'], [T.A.opps_per_100_accounts, T.B.opps_per_100_accounts, T.C.opps_per_100_accounts], i => [C.ultra, C.ultraMid, C.slateSoft][i]);
  s7.addChart(pres.charts.BAR, t7.data, chartOpts({ x: 0.45, y: 2.72, w: 6.2, h: 2.62, barDir: 'col', barGrouping: 'clustered', barOverlapPct: 100,
    chartColors: t7.colors, valAxisMinVal: 0, valAxisMaxVal: 25, dataLabelFormatCode: '0.0;;;', dataLabelFontSize: 14, barGapWidthPct: 80 }));
  s7.addText(`Tier A won ${T.A.post_launch_wins} of ${winsAll} post-launch deals.`, { x: X0, y: 5.42, w: 6.0, h: 0.34, fontFace: F.body, fontSize: 14, bold: true, color: C.ink, margin: 0, isTextBox: true });
  panelTitle(s7, 7.15, 2.05, 5.58, 'Launch scorecard since March 23', 'Actual against plan to date');
  const tone = st => (st === 'On track' ? [C.moss, C.mossSoft] : st === 'Watch' ? [C.amber, C.amberSoft] : [C.crimson, C.crimsonSoft]);
  s7.addTable([
    [headCell('Metric'), headCell('Attainment', { align: 'right' }), headCell('Status', { align: 'center' })],
    ...D.launch_lines.map(l => {
      const [fg, bg] = tone(l.status);
      return [cell(l.metric), cell(pct(l.attainment), { align: 'right', bold: true }), cell(l.status, { align: 'center', bold: true, color: fg, fill: { color: bg } })];
    }),
  ], { x: 7.15, y: 2.75, w: 5.58, colW: [2.9, 1.28, 1.4], rowH: 0.37 });
  soWhat(s7, 'Add SE capacity or a packaged 30-day POV kit before more top-of-funnel spend, and run a JAPAC certification sprint.');
  footer(s7, SYNTH, 7);
  const pov = D.launch_lines.find(l => l.metric === 'POVs started');
  s7.addNotes(`This maps to the launch and enablement part of the role. The ICP was built only from accounts that bought before the March 23 relaunch, then tested on deals created afterward. Tier A produced ${T.A.opps_per_100_accounts} deals per 100 accounts against ${T.C.opps_per_100_accounts} for Tier C, and won ${T.A.post_launch_wins} of ${winsAll} post-launch deals. That out-of-time test is what makes it usable for routing. The constraint is proof of value: POV starts are at ${pct(pov.attainment)} of plan, and ${pct(D.launch_totals.lost_at_pov_share)} of losses happen at that stage. So I'd add SE capacity or a packaged 30-day POV before spending more on top of funnel.`);

  /* 8. The plan */
  const s8 = pres.addSlide();
  header(s8, 'The plan', `Four moves close the gap: two plays, ${D.rec_hires} specialist hires, and one pipeline sprint.`);
  panelTitle(s8, X0, 2.05, 5.2, 'FY27 bookings, modeled', `Against the ${money(D.fy27_target)} target`);
  const r1 = v => Math.round(v / 1e5) / 10;               // $M to one decimal
  const baseM = r1(D.baseline_forecast), playsM = r1(D.plays_forecast - D.baseline_forecast), hiresM = r1(D.rec_forecast - D.plays_forecast);
  const p8 = colorSeries(['Current path', 'With the two plays', `Plus ${D.rec_hires} hires`, 'FY27 target'],
    [baseM, +(baseM + playsM).toFixed(1), +(baseM + playsM + hiresM).toFixed(1), r1(D.fy27_target)], i => [C.slate, C.ultraMid, C.ultra, C.ink][i]);
  s8.addChart(pres.charts.BAR, p8.data, chartOpts({ x: 0.45, y: 2.72, w: 5.35, h: 2.8, barDir: 'col', barGrouping: 'clustered', barOverlapPct: 100,
    chartColors: p8.colors, valAxisMinVal: 0, valAxisMaxVal: 76, dataLabelFormatCode: '$0.0"M";;;', dataLabelFontSize: 13, catAxisLabelFontSize: 11, barGapWidthPct: 55 }));
  s8.addText(`The plays add $${playsM.toFixed(1)}M; ${D.rec_hires} hires add $${hiresM.toFixed(1)}M.`,
    { x: X0, y: 5.55, w: 5.2, h: 0.3, fontFace: F.body, fontSize: 11.5, color: C.slate2, margin: 0, isTextBox: true });
  s8.addTable([
    [headCell('Action'), headCell('Owners'), headCell('When'), headCell('Worth')],
    [cell('Make SD-WAN the default in every Zscaler and Netskope deal', { bold: true }), cell('Product Marketing, Sales'), cell('Q2 kickoff'), cell(`+${lev.bundle_pts} pts win rate`)],
    [cell('Run a renewal-timed attach play', { bold: true }), cell('GTM Strategy, Sales Ops'), cell('October'), cell(`+${lev.renewal_pts} pts win rate`)],
    [cell(`Approve ${D.rec_hires} SASE specialists for JAPAC and EMEA mid-market`, { bold: true }), cell('Sales leadership, Finance'), cell('This month'), cell(`${money(D.rec_run_rate)} a year once ramped`)],
    [cell('Q2 pipeline sprint with Marketing and Partners', { bold: true }), cell('Marketing, Partners'), cell('By Nov 15'), cell('+$1.0M a week of pipeline')],
  ], { x: 6.25, y: 2.05, w: 6.48, colW: [2.45, 1.4, 1.3, 1.33], rowH: [0.36, 0.62, 0.5, 0.62, 0.62], fontSize: 11.5 });
  s8.addText(`The ${D.rec_hires} hires cost ${money(D.rec_cost)} in FY27. Hiring alone would take ${D.hire_only} hires and ${money(D.hire_only_cost)}.`,
    { x: 6.25, y: 5.12, w: 6.48, h: 0.55, fontFace: F.body, fontSize: 13, color: C.ink, margin: 0, isTextBox: true, valign: 'top' });
  soWhat(s8, `One decision is needed this month: the ${D.rec_hires} specialist requisitions. Everything else starts at the Q2 kickoff.`);
  footer(s8, SYNTH, 8);
  s8.addNotes(`Current path: ${money(D.baseline_forecast)} against a ${money(D.fy27_target)} target. The two plays add ${money(D.plays_forecast - D.baseline_forecast)} with no headcount; ${D.rec_hires} specialists add ${money(D.rec_forecast - D.plays_forecast)}, for ${money(D.rec_cost)} in FY27 and ${money(D.rec_run_rate)} of annual capacity once ramped. The alternative, hiring only, takes ${D.hire_only} specialists and ${money(D.hire_only_cost)}. Walk the table owner by owner: this is where you show you know who has to say yes. The interactive planning simulator lets anyone change productivity, ramp, attrition, or lead time and see this recalculate.`);

  /* 9. Risks */
  const s9 = pres.addSlide();
  header(s9, 'Risks', "The plan doesn't hang on one bet, and the biggest assumption gets tested before we scale it.");
  await iconRow(s9, Fi.FiShuffle, X0, 2.12, 'Selection, not coverage', 'Covered territories may simply have been stronger. A staggered pilot separates the two.', 6.0);
  await iconRow(s9, Fi.FiUsers, X0, 3.32, 'Comp and channel conflict', 'Overlay specialists double-credit core sellers and can crowd partners. Rules of engagement come before hiring.', 6.0);
  await iconRow(s9, Fi.FiClock, X0, 4.52, 'Ramp and discounting', `If hiring slips to six months, the plan still lands at ${pct(D.slip_attainment)}. Watch that bundle discounts don't eat deal size.`, 6.0);
  s9.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.8, y: 2.05, w: 4.93, h: 3.72, fill: { color: C.chalk }, line: { color: C.chalk }, rectRadius: 0.12 });
  s9.addText("How I'd test the biggest assumption", { x: 8.05, y: 2.22, w: 4.5, h: 0.32, fontFace: F.body, fontSize: 15, bold: true, color: C.ink, margin: 0, isTextBox: true });
  s9.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.05, y: 2.75, w: 2.12, h: 1.3, fill: { color: C.ultraSoft }, line: { color: C.ultraSoft }, rectRadius: 0.08 });
  s9.addText('Half of eligible uncovered territories get a specialist', { x: 8.15, y: 2.75, w: 1.92, h: 1.3, fontFace: F.body, fontSize: 12.5, color: C.ink, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
  s9.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 10.38, y: 2.75, w: 2.12, h: 1.3, fill: { color: C.white }, line: { color: C.slateSoft, width: 1 }, rectRadius: 0.08 });
  s9.addText('The other half stay as they are, as the control group', { x: 10.48, y: 2.75, w: 1.92, h: 1.3, fontFace: F.body, fontSize: 12.5, color: C.ink, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
  s9.addShape(pres.shapes.LINE, { x: 9.11, y: 4.07, w: 0, h: 0.3, line: { color: C.slate2, width: 1.5, endArrowType: 'triangle' } });
  s9.addShape(pres.shapes.LINE, { x: 11.44, y: 4.07, w: 0, h: 0.3, line: { color: C.slate2, width: 1.5, endArrowType: 'triangle' } });
  s9.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.05, y: 4.42, w: 4.45, h: 1.12, fill: { color: C.white }, line: { color: C.ultra, width: 1.25 }, rectRadius: 0.08 });
  s9.addText('After two quarters, compare attach. Scale coverage in FY28 only if the gap closes.', { x: 8.2, y: 4.42, w: 4.15, h: 1.12, fontFace: F.body, fontSize: 13, bold: true, color: C.ink, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
  soWhat(s9, 'The plays work without the hires, and the pilot decides whether coverage scales in FY28.');
  footer(s9, SYNTH, 9);
  s9.addNotes(`This is the slide that earns trust. The biggest risk is that the coverage effect is selection: leadership may have covered the territories that were already stronger. I can't rule that out from this data, so I'd test it: add specialists to half of the eligible uncovered territories, hold the other half out, compare attach after two quarters. Second, overlay specialists create comp and channel conflict; rules of engagement come first. Third, ramp: if hiring lead time slips to six months, the plan still lands at ${pct(D.slip_attainment)} because the plays carry it. Watch bundle discounting so win-rate gains don't come out of deal size.`);

  /* 10. First 90 days */
  const s10 = pres.addSlide();
  header(s10, 'First 90 days', 'First 90 days: trusted numbers, two plays live, and a pilot that settles the coverage question.');
  const colsX = [X0, 4.72, 8.84];
  s10.addShape(pres.shapes.LINE, { x: colsX[0] + 0.32, y: 2.42, w: colsX[2] - colsX[0], h: 0, line: { color: C.haze, width: 2 } });
  const phases = [
    ['30', 'Days 1 to 30: learn and rebuild', ['Meet Sales, Product Marketing, Sales Ops, and Finance leads; agree on metric definitions', 'Rebuild the weekly business review on real CRM data', 'Re-test the coverage and SD-WAN findings on real deals']],
    ['60', 'Days 31 to 60: launch', ['Start the renewal-timed attach play in two regions', 'Design the coverage pilot with Sales Ops and Finance', 'Run the Q2 pipeline sprint cadence with Marketing']],
    ['90', 'Days 61 to 90: plan and prove', ['Reforecast FY27 capacity with actual ramp and attrition', 'Bring FY28 planning inputs: capacity model and territory options', "First quarterly review, including the pilot's early read"]],
  ];
  phases.forEach(([n, head, items], i) => {
    const x = colsX[i];
    s10.addShape(pres.shapes.OVAL, { x, y: 2.1, w: 0.64, h: 0.64, fill: { color: C.ultra }, line: { color: C.ultra } });
    s10.addText(n, { x, y: 2.1, w: 0.64, h: 0.64, fontFace: F.head, fontSize: 15, bold: true, color: C.white, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
    s10.addText(head, { x, y: 2.95, w: 3.85, h: 0.36, fontFace: F.body, fontSize: 15, bold: true, color: C.ink, margin: 0, isTextBox: true });
    s10.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })),
      { x, y: 3.4, w: 3.85, h: 1.8, fontFace: F.body, fontSize: 13, color: C.ink2, margin: 0, isTextBox: true, valign: 'top', paraSpaceAfter: 8 });
  });
  s10.addText('Operating rhythm from week one', { x: X0, y: 5.4, w: 2.6, h: 0.36, fontFace: F.body, fontSize: 13, bold: true, color: C.ink, margin: 0, isTextBox: true, valign: 'middle' });
  [['Weekly business review', 1.95], ['Monthly business review', 2.05], ['Quarterly business review', 2.15], ['FY28 planning from February', 2.35]]
    .reduce((x, [label, w]) => { pill(s10, label, C.chalk, C.ink, x, 5.4, w); return x + w + 0.15; }, 3.3);
  soWhat(s10, 'The first deliverable is trust in the numbers; the weekly, monthly, and quarterly reviews run on them from week one.');
  footer(s10, 'Assumes CRM and planning data access in week one.', 10);
  s10.addNotes('Hiring managers want to know what happens on Monday. First 30 days: learn the business and agree on definitions before building anything, rebuild the weekly review on real data, and re-test my two biggest findings on real deals. It is fine if they change. Days 31 to 60: launch the renewal-timed play in two regions and design the coverage pilot with Sales Ops and Finance. Days 61 to 90: reforecast capacity with real ramp and attrition and bring FY28 planning inputs, since FY28 planning starts in February.');

  /* 11. How I'd work (close) */
  const s11 = pres.addSlide();
  s11.background = { color: C.ink };
  header(s11, 'How I work', "How I'd work on your team", true, 32);
  const principles = [
    [Fi.FiTarget, 'Answer first', 'Every readout starts with the number and the ask, then the evidence. This deck is the format.'],
    [Fi.FiLayers, 'Systems over heroics', 'The weekly review drafts itself, and data-quality checks run before anyone sees a chart, so the team spends its time on decisions.'],
    [Fi.FiCompass, 'Say what would change my mind', 'Every recommendation ships with its risks and a test, like the coverage pilot, not just a conclusion.'],
  ];
  for (let i = 0; i < principles.length; i++) {
    const [Icon, head, body] = principles[i];
    const x = colsX[i];
    s11.addShape(pres.shapes.OVAL, { x, y: 2.2, w: 0.72, h: 0.72, fill: { color: C.ultra }, line: { color: C.ultra } });
    s11.addImage({ data: await iconData(Icon, C.white), x: x + 0.18, y: 2.38, w: 0.36, h: 0.36 });
    s11.addText(head, { x, y: 3.12, w: 3.85, h: 0.4, fontFace: F.body, fontSize: 18, bold: true, color: C.white, margin: 0, isTextBox: true });
    s11.addText(body, { x, y: 3.6, w: 3.7, h: 1.5, fontFace: F.body, fontSize: 14, color: C.haze, margin: 0, isTextBox: true, valign: 'top' });
  }
  const link = D.github || 'github.com/YOUR-USERNAME/sase-gtm-os';
  s11.addText([
    { text: 'Explore the live model and the code', options: { bold: true, color: C.white, breakLine: true } },
    { text: link, options: D.github ? { color: C.ultraPale, hyperlink: { url: /^https?:/.test(D.github) ? D.github : `https://${D.github}` } } : { color: C.ultraPale } },
  ], { x: X0, y: 5.45, w: 8, h: 0.75, fontFace: F.body, fontSize: 15, margin: 0, isTextBox: true, valign: 'top' });
  s11.addText(D.author, { x: W - X0 - 4, y: 5.45, w: 4, h: 0.4, fontFace: F.body, fontSize: 15, bold: true, color: C.white, align: 'right', margin: 0, isTextBox: true });
  footer(s11, 'Independent exercise: synthetic deals, real market data. Not affiliated with or endorsed by Palo Alto Networks.', 11, true);
  s11.addNotes('Close on how you work, not on a thank-you slide. Three habits, each with proof in the room: answer first (this deck), systems over heroics (the weekly review that drafts itself, the data-quality gate), and saying what would change your mind (the pilot). Then offer the live model: "If it helps, I can walk you through the planning simulator with your own assumptions." Stop talking and take questions.');

  /* 12. Appendix */
  const s12 = pres.addSlide();
  header(s12, 'Appendix', "How the model works, and what's real.");
  const tiles = [
    [int(D.accounts), 'synthetic firewall accounts, simulated quarter by quarter from FY24'],
    [int(D.clean_opps), `deals validated; ${D.quarantined} quarantined by automated data-quality checks`],
    [D.auc.toFixed(2), `cross-validated AUC; logistic regression beat gradient boosting (${D.auc_gbm.toFixed(2)})`],
    ['5 of 5', 'planning scenarios reproduced exactly by the interactive app, checked by automated tests'],
  ];
  tiles.forEach(([big, label], i) => {
    const x = X0 + (i % 2) * 2.95, y = 2.05 + Math.floor(i / 2) * 1.85;
    s12.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.75, h: 1.65, fill: { color: C.chalk }, line: { color: C.chalk }, rectRadius: 0.1 });
    s12.addText(big, { x: x + 0.22, y: y + 0.15, w: 2.35, h: 0.6, fontFace: F.head, fontSize: 30, bold: true, color: C.ink, margin: 0, isTextBox: true, valign: 'middle' });
    s12.addText(label, { x: x + 0.22, y: y + 0.8, w: 2.35, h: 0.75, fontFace: F.body, fontSize: 12, color: C.ink2, margin: 0, isTextBox: true, valign: 'top' });
  });
  const list = (title, items, y) => {
    s12.addText(title, { x: 6.8, y, w: 5.93, h: 0.34, fontFace: F.body, fontSize: 15, bold: true, color: C.ink, margin: 0, isTextBox: true });
    s12.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })),
      { x: 6.8, y: y + 0.4, w: 5.93, h: items.length * 0.36 + 0.1, fontFace: F.body, fontSize: 13, color: C.ink2, margin: 0, isTextBox: true, valign: 'top', paraSpaceAfter: 4 });
  };
  list('Synthetic, and calibrated to public figures', ['Accounts, deals, sellers, territories, and launch data', 'Every planted pattern disclosed in the methodology'], 2.05);
  list('Real, and sourced', ['Competitor ARR: Palo Alto Networks, Zscaler, Fortinet, and Netskope earnings releases',
    "SASE market size, growth, and forecast: Dell'Oro Group", 'SASE bookings growth and displacements: Palo Alto Networks Q4 FY26 earnings call',
    'Automated feeds in the repository: SEC EDGAR, CISA KEV, Census business statistics'], 3.3);
  footer(s12, 'Full methodology, source links, and code: docs/methodology.md in the repository.', 12);
  s12.addNotes(`Use this only in Q&A. The deals are synthetic because real CRM data is confidential; the book is calibrated to Palo Alto Networks' public growth figures, and every planted pattern is disclosed. ${int(D.clean_opps)} deals passed validation and ${D.quarantined} were quarantined by automated checks before reaching any metric. The propensity model is a logistic regression with a cross-validated AUC of ${D.auc.toFixed(2)}; gradient boosting scored ${D.auc_gbm.toFixed(2)}, so the simpler, explainable model won. The interactive app and the Python pipeline are tested to produce identical numbers.`);

  await pres.writeFile({ fileName: OUT });
  console.log(`wrote ${OUT}`);
}

build().catch(err => { console.error(err); process.exit(1); });
