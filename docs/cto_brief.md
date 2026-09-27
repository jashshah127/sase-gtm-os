# Brief for cto.new: public-data fetch and weekly refresh

Paste everything below the line into cto.new **Chat** first, review the plan it proposes, then run it
as a **Task**. Replace `jashshah127` where it appears. The SEC contact goes in a repository secret,
never in code.

---

You're working in my repo `sase-gtm-os`: a static site (`index.html` at the repo root) built by a
Python pipeline in `pipeline/`. I will personally review every change, so optimize for reviewability
over cleverness.

GROUND RULES
- Work on a branch. Open one pull request per phase below. Never push to main.
- Only ADD these files: `pipeline/fetch_public_data.py`, `tests/test_fetch_public_data.py`,
  `tests/fixtures/` (sample responses), `data/public/` (fetched outputs), and in Phase 2
  `.github/workflows/refresh.yml`. Do not modify or delete any existing file.
- Never touch `data/curated/` (hand-curated figures) or `tests/fixtures_market/` (fake fixtures for
  another test).
- Never fabricate, estimate, or hand-type data. Every row must come from the source. If your
  environment can't reach a source, say so in the PR instead.
- No secrets or emails in code. Read the SEC contact from the environment variable `SEC_USER_AGENT`
  and exit with a clear error if it's missing.
- Python 3.11, using only `requests` and `pandas` (already in requirements.txt).
- Every PR description must include: what changed and why, every file added, step-by-step local
  verification, and every assumption you made.

PHASE 1 (PR 1): `pipeline/fetch_public_data.py` + tests
Write real public data to `data/public/` (create the folder). `pipeline/market.py` already reads
these files and checks them against these exact columns, so match them exactly.

1. `sec_financials.csv`
   Source: SEC EDGAR companyfacts API, https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json
   Tickers: PANW, ZS, FTNT, NTSK, NET, CSCO, CHKP, CRWD (resolve CIKs from the SEC's
   company_tickers.json). Stay under 10 requests per second.
   Concepts: Revenues, RevenueFromContractWithCustomerExcludingAssessedTax, DeferredRevenueCurrent,
   DeferredRevenueNoncurrent, RevenueRemainingPerformanceObligation. Forms 10-K and 10-Q only.
   Columns: ticker, cik, concept, fiscal_year, fiscal_period, form, period_start, period_end,
   value_usd, filed. Dates as YYYY-MM-DD; period_start blank for point-in-time values.

2. `kev_edge_vendors.csv`
   Source: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
   Vendors: Palo Alto Networks, Fortinet, Ivanti, Cisco, SonicWall, Citrix, Check Point, F5,
   Juniper, Zscaler (match on the feed's vendorProject field).
   Columns: cve_id, vendor, product, vulnerability_name, date_added, known_ransomware_use
   (keep the feed's values, for example Known or Unknown).

3. `census_susb.csv`
   Source: the latest Census Statistics of U.S. Businesses annual dataset, US totals by NAICS sector
   and enterprise employment size, including the detailed large-firm bands up to 20,000+. Start at
   https://www.census.gov/data/datasets/2022/econ/susb/2022-susb.html
   Columns: year, naics, naics_label, size_band, firms, establishments, employment.
   Keep the Census size-band labels as published (for example "<20", "500-749", "20,000+", "Total")
   and keep the all-industry total rows. In the PR, name the exact file and year used and explain
   your column mapping.

4. `manifest.json`: an object keyed by file name (for example "sec_financials.csv"), each with
   source_url, fetched_at (UTC, ISO 8601), and rows.

Behavior: retries with backoff; non-zero exit with a clear message if a source is unreachable or
changes shape; idempotent; one summary line per file; an `--only sec|kev|census` flag.
Tests: `tests/test_fetch_public_data.py` using small saved sample responses in `tests/fixtures/` so
tests run offline. Cover parsing, vendor filtering, and exact output columns.
Commit the four files from a real run so I can inspect the data.

Acceptance for PR 1:
- `python pipeline/market.py` prints `loaded` for sec, kev, and census.
- `python tests/test_market.py` and your new tests pass.
- `python pipeline/run_all.py` completes.

PHASE 2 (PR 2, only after I merge PR 1): weekly refresh
`.github/workflows/refresh.yml`, triggered Mondays 12:00 UTC and manually. Steps: checkout; Python
3.11 with pip cache; `pip install -r requirements.txt`; `python pipeline/fetch_public_data.py`
(SEC_USER_AGENT from the repository secret); `python pipeline/run_all.py`; commit changes under
`data/`, `docs/`, and `index.html` only if something changed, message
"chore: weekly public data refresh".
Use `permissions: contents: write`, pinned action versions, and a concurrency group. GitHub Pages
deploys from main. Verify the site actually redeploys after the bot's commit. If pushes made with
GITHUB_TOKEN don't trigger the Pages build, switch to actions/upload-pages-artifact +
actions/deploy-pages and tell me exactly which Pages setting to change.

Acceptance for PR 2: a manual run is green, and the live site at
https://jashshah127.github.io/sase-gtm-os/#market shows the three public-data panels loaded.
