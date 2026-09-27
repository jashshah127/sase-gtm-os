/* Hand-rolled SVG charts. No dependencies, so the app works offline and loads instantly.
   Every mark carries a data-tip attribute; main.js shows it on hover. */
function niceMax(v) {
  if (!(v > 0)) return 1;
  const e = Math.pow(10, Math.floor(Math.log10(v))), f = v / e;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * e;
}
const tickVals = (max, n = 4) => Array.from({ length: n + 1 }, (_, i) => (max * i) / n);
const trunc = (s, n) => { s = String(s); return s.length > n ? s.slice(0, Math.max(1, n - 1)) + '…' : s; };
const tipA = t => (t ? ` data-tip="${esc(t)}"` : '');
const svgDoc = (W, H, body, aria) =>
  `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="${esc(aria || 'Chart')}" style="max-width:100%;height:auto">${body}</svg>`;
const widthOf = el => Math.max(260, Math.floor(el.clientWidth || el.getBoundingClientRect().width || 600));
function hexRgb(c) { const n = parseInt(c.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
function mix(c1, c2, t) {
  const a = hexRgb(c1), b = hexRgb(c2), k = clamp(t, 0, 1);
  return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * k)).join(',')})`;
}

const Charts = {
  /* rows: [{label, value, color, tip, text}] */
  hbar(el, rows, o = {}) {
    const W = widthOf(el), rowH = o.rowH || 30, axis = o.axis !== false;
    const top = o.refLabel ? 20 : 4, bottom = axis ? 24 : 4;
    const labelW = o.labelW ? Math.min(o.labelW, Math.round(W * 0.5)) : Math.min(210, Math.round(W * 0.36));
    const valW = o.valW || 64, plotW = Math.max(40, W - labelW - valW - 8);
    const f = o.fmt || (v => String(v));
    const max = o.max || niceMax(Math.max(0, ...rows.map(r => r.value), o.ref || 0));
    const x = v => labelW + (clamp(v, 0, max) / max) * plotW;
    const H = top + rows.length * rowH + bottom;
    let s = '';
    if (axis) for (const t of tickVals(max, 4)) {
      s += `<line class="gl" x1="${x(t).toFixed(1)}" x2="${x(t).toFixed(1)}" y1="${top}" y2="${H - bottom}"/>`;
      s += `<text class="tick" x="${x(t).toFixed(1)}" y="${H - 7}" text-anchor="middle">${esc((o.tickFmt || f)(t))}</text>`;
    }
    rows.forEach((r, i) => {
      const cy = top + i * rowH + rowH / 2, bh = Math.min(18, rowH - 10);
      s += `<text class="lbl" x="${labelW - 10}" y="${cy}" dy=".35em" text-anchor="end">${esc(trunc(r.label, Math.floor((labelW - 12) / 6.3)))}</text>`;
      s += `<rect x="${labelW}" y="${(cy - bh / 2).toFixed(1)}" width="${Math.max(1.5, x(r.value) - labelW).toFixed(1)}" height="${bh}" rx="2" fill="${r.color || PAL.ultra}"${tipA(r.tip || `${r.label}: ${f(r.value)}`)}/>`;
      s += `<text class="val" x="${(x(r.value) + 6).toFixed(1)}" y="${cy}" dy=".35em">${esc(r.text ?? f(r.value))}</text>`;
    });
    if (o.ref != null) {
      s += `<line class="ref" x1="${x(o.ref).toFixed(1)}" x2="${x(o.ref).toFixed(1)}" y1="${top - 4}" y2="${H - bottom}"/>`;
      if (o.refLabel) s += `<text class="ref-lbl" x="${x(o.ref).toFixed(1)}" y="12" text-anchor="middle">${esc(o.refLabel)}</text>`;
    }
    el.innerHTML = svgDoc(W, H, s, o.aria);
  },

  /* series: [{name, values, color, colors, tips, labels}], stacked or grouped */
  vbar(el, cats, series, o = {}) {
    const W = widthOf(el), H = o.h || 240;
    const longest = Math.max(...cats.map(c => String(c).length));
    const rot = o.rotate ?? (!o.labelEvery && (W - 70) / cats.length < longest * 6.6 + 10);
    const m = { t: 18, r: 10, b: rot ? 56 : 28, l: o.yW || 56 };
    const pw = W - m.l - m.r, ph = H - m.t - m.b;
    const stacked = !!o.stacked, f = o.fmt || (v => String(v));
    let mx = 0;
    cats.forEach((_, i) => {
      if (stacked) mx = Math.max(mx, sum(series, se => se.values[i] || 0));
      else for (const se of series) mx = Math.max(mx, se.values[i] || 0);
    });
    for (const l of o.lines || []) for (const v of l.values) if (v != null) mx = Math.max(mx, v);
    for (const r of o.refs || []) mx = Math.max(mx, r.value);
    const max = o.max || niceMax(mx * 1.1);
    const y = v => m.t + ph - (clamp(v, 0, max) / max) * ph;
    const band = pw / cats.length, gap = Math.min(20, band * 0.3);
    const bw = stacked ? band - gap : (band - gap) / series.length;
    let s = '';
    for (const t of tickVals(max, 4)) {
      s += `<line class="gl" x1="${m.l}" x2="${W - m.r}" y1="${y(t).toFixed(1)}" y2="${y(t).toFixed(1)}"/>`;
      s += `<text class="tick" x="${m.l - 8}" y="${y(t).toFixed(1)}" dy=".32em" text-anchor="end">${esc((o.tickFmt || f)(t))}</text>`;
    }
    cats.forEach((c, i) => {
      const x0 = m.l + i * band + gap / 2;
      let base = 0;
      series.forEach((se, j) => {
        const v = se.values[i];
        if (v == null || (v <= 0 && !se.labels)) return;
        const bx = stacked ? x0 : x0 + j * bw;
        const y1 = stacked ? y(base + v) : y(v), y0 = stacked ? y(base) : y(0);
        const tip = (se.tips && se.tips[i]) || `${c}${se.name ? '\n' + se.name : ''}: ${f(v)}`;
        const w = Math.max(1, bw - (stacked || series.length === 1 ? 0 : 2));
        s += `<rect x="${bx.toFixed(1)}" y="${y1.toFixed(1)}" width="${w.toFixed(1)}" height="${Math.max(0, y0 - y1).toFixed(1)}" rx="1.5" fill="${(se.colors && se.colors[i]) || se.color || PAL.ultra}"${tipA(tip)}/>`;
        if (o.valueLabels && !stacked) {
          const txt = se.labels ? se.labels[i] : o.valueLabels(v);
          s += `<text class="val" x="${(bx + w / 2).toFixed(1)}" y="${(y1 - 6).toFixed(1)}" text-anchor="middle">${esc(txt)}</text>`;
        }
        if (stacked) base += v;
      });
      const every = o.labelEvery || 1;
      if ((cats.length - 1 - i) % every === 0) {
        const lx = (m.l + i * band + band / 2).toFixed(1);
        s += rot
          ? `<text class="tick" transform="translate(${lx},${H - m.b + 14}) rotate(-38)" text-anchor="end">${esc(c)}</text>`
          : `<text class="tick" x="${lx}" y="${H - m.b + 17}" text-anchor="middle">${esc(c)}</text>`;
      }
    });
    for (const l of o.lines || []) {
      let d = '';
      l.values.forEach((v, i) => { if (v == null) return; d += `${d ? 'L' : 'M'}${(m.l + i * band + band / 2).toFixed(1)},${y(v).toFixed(1)}`; });
      s += `<path d="${d}" fill="none" stroke="${l.color || PAL.ink}" stroke-width="${l.width || 2}"${l.dashed ? ' stroke-dasharray="5 4"' : ''} stroke-linejoin="round" pointer-events="none"/>`;
    }
    for (const r of o.refs || []) {
      s += `<line class="ref" x1="${m.l}" x2="${W - m.r}" y1="${y(r.value).toFixed(1)}" y2="${y(r.value).toFixed(1)}"/>`;
      if (r.label) s += `<text class="ref-lbl" x="${W - m.r}" y="${(y(r.value) - 6).toFixed(1)}" text-anchor="end">${esc(r.label)}</text>`;
    }
    el.innerHTML = svgDoc(W, H, s, o.aria);
  },

  /* series: [{name, values (null = gap), color, dashed, width, dots}] */
  line(el, labels, series, o = {}) {
    const W = widthOf(el), H = o.h || 240;
    const m = { t: 18, r: o.rPad || 16, b: 28, l: o.yW || 56 };
    const pw = W - m.l - m.r, ph = H - m.t - m.b, f = o.fmt || (v => String(v));
    let mx = 0;
    for (const se of series) for (const v of se.values) if (v != null) mx = Math.max(mx, v);
    for (const r of o.refs || []) mx = Math.max(mx, r.value);
    const lo = o.min ?? 0, max = o.max || niceMax(mx * 1.08);
    const x = i => m.l + (labels.length < 2 ? pw / 2 : (i * pw) / (labels.length - 1));
    const y = v => m.t + ph - ((clamp(v, lo, max) - lo) / (max - lo || 1)) * ph;
    let s = '';
    for (let k = 0; k <= 4; k++) {
      const t = lo + ((max - lo) * k) / 4;
      s += `<line class="gl" x1="${m.l}" x2="${W - m.r}" y1="${y(t).toFixed(1)}" y2="${y(t).toFixed(1)}"/>`;
      s += `<text class="tick" x="${m.l - 8}" y="${y(t).toFixed(1)}" dy=".32em" text-anchor="end">${esc((o.tickFmt || f)(t))}</text>`;
    }
    const every = o.labelEvery || Math.max(1, Math.ceil(labels.length / Math.max(2, Math.floor(pw / 62))));
    labels.forEach((lb, i) => {
      if ((labels.length - 1 - i) % every === 0) s += `<text class="tick" x="${x(i).toFixed(1)}" y="${H - 9}" text-anchor="middle">${esc(lb)}</text>`;
    });
    for (const r of o.refs || []) {
      s += `<line class="ref" x1="${m.l}" x2="${W - m.r}" y1="${y(r.value).toFixed(1)}" y2="${y(r.value).toFixed(1)}"/>`;
      if (r.label) s += `<text class="ref-lbl" x="${W - m.r}" y="${(y(r.value) - 6).toFixed(1)}" text-anchor="end">${esc(r.label)}</text>`;
    }
    for (const se of series) {
      let d = '', on = false;
      se.values.forEach((v, i) => {
        if (v == null) { on = false; return; }
        d += `${on ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
        on = true;
      });
      s += `<path d="${d}" fill="none" stroke="${se.color}" stroke-width="${se.width || 2.2}"${se.dashed ? ' stroke-dasharray="6 5"' : ''} stroke-linejoin="round" stroke-linecap="round" pointer-events="none"/>`;
      if (se.dots) se.values.forEach((v, i) => { if (v != null) s += `<circle cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}" r="3" fill="${se.color}" pointer-events="none"/>`; });
    }
    const slot = labels.length < 2 ? pw : pw / (labels.length - 1);
    labels.forEach((lb, i) => {
      const vals = series.filter(se => se.values[i] != null && se.name).map(se => `${se.name}: ${f(se.values[i])}`);
      if (!vals.length) return;
      s += `<rect x="${(x(i) - slot / 2).toFixed(1)}" y="${m.t}" width="${slot.toFixed(1)}" height="${ph}" fill="transparent"${tipA(`${lb}\n${vals.join('\n')}`)}/>`;
    });
    el.innerHTML = svgDoc(W, H, s, o.aria);
  },

  /* cells[r][c] = {v, n, tip} */
  heat(el, rowLabels, colLabels, cells, o = {}) {
    const W = widthOf(el), labelW = Math.min(o.labelW || 150, Math.round(W * 0.34));
    const headH = 28, cellH = o.cellH || 30, cw = (W - labelW) / colLabels.length;
    const H = headH + rowLabels.length * cellH + 2, [lo, hi] = o.domain || [0, 1];
    let s = '';
    colLabels.forEach((c, j) => { s += `<text class="tick" x="${(labelW + j * cw + cw / 2).toFixed(1)}" y="17" text-anchor="middle">${esc(trunc(c, Math.floor(cw / 6.2)))}</text>`; });
    rowLabels.forEach((r, i) => {
      const y0 = headH + i * cellH;
      s += `<text class="lbl" x="${labelW - 10}" y="${y0 + cellH / 2}" dy=".35em" text-anchor="end">${esc(trunc(r, Math.floor((labelW - 12) / 6.3)))}</text>`;
      colLabels.forEach((_, j) => {
        const cell = cells[i][j], x0 = labelW + j * cw;
        if (!cell || !cell.n) {
          s += `<rect x="${(x0 + 1).toFixed(1)}" y="${y0 + 1}" width="${(cw - 2).toFixed(1)}" height="${cellH - 2}" rx="3" fill="#F4F6F9"/>`;
          s += `<text class="cell-txt" x="${(x0 + cw / 2).toFixed(1)}" y="${y0 + cellH / 2}" dy=".35em" text-anchor="middle" fill="${PAL.slate}">–</text>`;
          return;
        }
        const t = (cell.v - lo) / (hi - lo || 1);
        s += `<rect x="${(x0 + 1).toFixed(1)}" y="${y0 + 1}" width="${(cw - 2).toFixed(1)}" height="${cellH - 2}" rx="3" fill="${mix('#EEF0FB', PAL.ultra, t)}"${tipA(cell.tip)}/>`;
        s += `<text class="cell-txt" x="${(x0 + cw / 2).toFixed(1)}" y="${y0 + cellH / 2}" dy=".35em" text-anchor="middle" fill="${t > 0.55 ? '#fff' : PAL.ink}" pointer-events="none">${esc((o.fmt || String)(cell.v))}</text>`;
      });
    });
    el.innerHTML = svgDoc(W, H, s, o.aria);
  },

  /* pts: [{x, y, r, color, tip}] */
  scatter(el, pts, o = {}) {
    const W = widthOf(el), H = o.h || 300, m = { t: 14, r: 16, b: 42, l: 58 };
    const pw = W - m.l - m.r, ph = H - m.t - m.b;
    const xMax = o.xMax || niceMax(Math.max(0.01, ...pts.map(p => p.x)) * 1.08);
    const yMax = o.yMax || niceMax(Math.max(0.01, ...pts.map(p => p.y)) * 1.08);
    const x = v => m.l + (clamp(v, 0, xMax) / xMax) * pw, y = v => m.t + ph - (clamp(v, 0, yMax) / yMax) * ph;
    const fx = o.xFmt || String, fy = o.yFmt || String;
    let s = '';
    for (const t of tickVals(xMax, 4)) s += `<line class="gl" x1="${x(t).toFixed(1)}" x2="${x(t).toFixed(1)}" y1="${m.t}" y2="${m.t + ph}"/><text class="tick" x="${x(t).toFixed(1)}" y="${m.t + ph + 16}" text-anchor="middle">${esc(fx(t))}</text>`;
    for (const t of tickVals(yMax, 4)) s += `<line class="gl" x1="${m.l}" x2="${m.l + pw}" y1="${y(t).toFixed(1)}" y2="${y(t).toFixed(1)}"/><text class="tick" x="${m.l - 8}" y="${y(t).toFixed(1)}" dy=".32em" text-anchor="end">${esc(fy(t))}</text>`;
    if (o.diagonal) {
      const dmax = Math.min(xMax, yMax);
      s += `<line class="ref" x1="${x(0)}" y1="${y(0)}" x2="${x(dmax).toFixed(1)}" y2="${y(dmax).toFixed(1)}"/>`;
      s += `<text class="ref-lbl" x="${(x(dmax) - 6).toFixed(1)}" y="${(y(dmax) + 16).toFixed(1)}" text-anchor="end">${esc(o.diagonalLabel || 'Actual equals modeled')}</text>`;
    }
    for (const p of pts) s += `<circle cx="${x(p.x).toFixed(1)}" cy="${y(p.y).toFixed(1)}" r="${(p.r || 5).toFixed(1)}" fill="${p.color}" fill-opacity=".72" stroke="#fff" stroke-width="1"${tipA(p.tip)}/>`;
    if (o.xLabel) s += `<text class="ax-lbl" x="${m.l + pw / 2}" y="${H - 6}" text-anchor="middle">${esc(o.xLabel)}</text>`;
    if (o.yLabel) s += `<text class="ax-lbl" transform="translate(14,${m.t + ph / 2}) rotate(-90)" text-anchor="middle">${esc(o.yLabel)}</text>`;
    el.innerHTML = svgDoc(W, H, s, o.aria);
  },
};
