/* Routing, navigation, tooltips, and start-up. */
const ROUTES = [
  { id: 'briefing', name: 'Briefing', desc: 'The answer on one page', view: viewBriefing },
  { id: 'market', name: 'Market context', desc: 'Real public data: competitors and growth', view: viewMarket },
  { id: 'revenue', name: 'Revenue intelligence', desc: 'Pipeline, attach, whitespace, win and loss', view: viewRevenue },
  { id: 'planning', name: 'Planning simulator', desc: 'Capacity, hiring, and territories', view: viewPlanning },
  { id: 'launch', name: 'Prisma Browser launch', desc: 'ICP, targets, scorecard, field kit', view: viewLaunch },
  { id: 'exec', name: 'Executive layer', desc: 'Weekly business review and memo', view: viewExec },
  { id: 'cadence', name: 'Operating cadence', desc: 'Metrics, rhythm, RACI, data quality', view: viewCadence },
];
let currentRoute = null;

function renderShell() {
  $('#nav').innerHTML = `<ul>${ROUTES.map(r => `<li><a href="#${r.id}" data-id="${r.id}"><span class="n">${esc(r.name)}</span><span class="d">${esc(r.desc)}</span></a></li>`).join('')}</ul>`;
  const links = Object.entries(D.meta.links || {});
  $('#rail-foot').innerHTML = `<p>Built by ${esc(D.meta.author)}</p>` +
    (links.length ? `<p class="rail-links">${links.map(([k, v]) => `<a href="${esc(v)}" rel="noopener">${esc(k)}</a>`).join('')}</p>` : '') +
    '<p>Synthetic data. Not affiliated with or endorsed by Palo Alto Networks.</p>';
}

function route() {
  const [id, sub] = (decodeURIComponent(location.hash.slice(1)) || 'briefing').split('/');
  const r = ROUTES.find(x => x.id === id) || ROUTES[0];
  if (r.id === 'revenue' && sub && REV_TABS.some(t => t[0] === sub)) S.revTab = sub;
  $$('#nav a').forEach(a => (a.dataset.id === r.id ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current')));
  const main = $('#main');
  main.innerHTML = `<div class="topbar"><span>Data as of ${esc(D.meta.asOfLabel)}, week ${D.meta.weekOfQuarter} of ${esc(D.meta.fiscalLabel)}</span>${r.id === 'market' ? '<span class="badge real">Real public data</span>' : '<span class="badge">Synthetic data</span>'}</div><div id="view"></div>`;
  CHARTS = [];
  r.view($('#view'));
  document.title = `${r.name} | SASE GTM Operating System`;
  if (currentRoute !== r.id) { window.scrollTo(0, 0); main.focus({ preventScroll: true }); }
  currentRoute = r.id;
}

(function init() {
  const tip = $('#tip');
  document.addEventListener('mousemove', e => {
    const t = e.target && e.target.closest ? e.target.closest('[data-tip]') : null;
    if (!t) { tip.hidden = true; return; }
    tip.textContent = t.getAttribute('data-tip');
    tip.hidden = false;
    const pad = 14, r = tip.getBoundingClientRect();
    let x = e.clientX + pad, y = e.clientY + pad;
    if (x + r.width > window.innerWidth - 8) x = e.clientX - r.width - pad;
    if (y + r.height > window.innerHeight - 8) y = e.clientY - r.height - pad;
    tip.style.left = `${Math.max(4, x)}px`;
    tip.style.top = `${Math.max(4, y)}px`;
  });
  document.addEventListener('scroll', () => { tip.hidden = true; }, { passive: true });
  window.addEventListener('resize', debounce(() => {
    CHARTS = CHARTS.filter(c => c.el.isConnected);
    CHARTS.forEach(c => c.draw(c.el));
  }, 120));
  window.addEventListener('hashchange', route);
  renderShell();
  route();
})();
