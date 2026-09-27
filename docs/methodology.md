# Methodology

This project is an independent, working model of the SASE Product GTM Manager role. Every account, deal, and seller in it is synthetic. Public Palo Alto Networks figures are used only to calibrate scale and growth, and are cited below. Nothing here is affiliated with or endorsed by Palo Alto Networks.

## Why synthetic data, and how it is kept honest

Real CRM data is confidential, so the data is simulated. The risk with simulated data is that an analysis just finds what was planted. Two safeguards: every planted pattern is disclosed below, and the analysis uses methods that would work unchanged on a real Salesforce export (the SQL in `sql/` targets BigQuery).

## Data model

| Table | Grain | Key fields |
|---|---|---|
| accounts | One firewall customer | segment, region, industry, territory, employees, branches, remote and contractor share, unmanaged devices, VDI, incumbent remote access, firewall renewal, Prisma products owned, SASE ARR |
| opportunities | One deal | type (land, expansion, browser), product, created and close dates, stage, amount, competitor, SD-WAN bundle, source, loss reason and stage, stage entry date, pushes, renewal alignment, POV start |
| territories | One core territory | region, segment, account count, SASE specialist coverage |
| specialists | One SASE overlay specialist | region, segment, hire date |
| launch_enablement_weekly | Region by week | field headcount, certified share |

## How the data is generated

4,200 firewall accounts are simulated quarter by quarter from FY23 Q3, using Palo Alto Networks' fiscal calendar (the fiscal year starts August 1). The dataset is frozen at September 25, 2026, week 8 of FY27 Q1. Each quarter, non-customers may open a land opportunity; its probability rises with the account's fit and with specialist coverage, and grows over time. Deals carry a competitor, an SD-WAN bundle decision, a source, a cycle length, and a win probability; they then move through stages, sometimes slip, and close. Customers generate expansion deals. Prisma Browser has early adopters before the relaunch and weekly pipeline after it.

### Planted patterns (disclosed so nothing is found by accident)

- Fit: larger segments, remote-heavy and contractor-heavy workforces, bigger branch footprints, Cortex ownership, and GlobalProtect VPN users are likelier to adopt. SSE incumbents (Zscaler, Netskope, and others) are much less likely.
- Coverage: territories with a SASE specialist create more opportunities and win more often. Coverage is thin in EMEA and JAPAC mid-market and commercial by design.
- Competition: win rates are lower against Zscaler and Netskope, and an SD-WAN bundle recovers a large part of that gap. The bundle helps only a little against other rivals.
- Timing: deals opened 90 to 270 days before the firewall renewal win more often.
- Partners: partner-sourced deals win more often in mid-market and commercial.
- Process: some deals stall in Technical Validation; some open deals carry placeholder close dates in later quarters.
- Browser: adoption rises with contractor share, unmanaged devices, VDI, industry, and existing Prisma Access.
- Competitor names are real so the analysis reads realistically. The win rates are synthetic and say nothing about any vendor's actual performance.

### Calibration to public figures

The simulation was tuned so the book looks like a plausible slice of the business: attach of 25.2%, FY26 SASE bookings growth of 35.5% (Palo Alto Networks reported 40% SASE bookings growth in FY26), and a land win rate of 36.4%.

## Data quality

Known issues are injected into the raw export, and `pipeline/validate.py` must catch every one before anything downstream runs. 31 opportunities were quarantined and duplicate accounts merged; past-due close dates are flagged for owners. The run fails if any injected issue is missed.

| Check | Rows failed | Action |
|---|---|---|
| Duplicate accounts | 9 | Merged into surviving record |
| Orphan opportunities | 11 | Quarantined |
| Close date before created date | 14 | Quarantined |
| Non-positive amount | 6 | Quarantined |
| Past-due close date on open deal | 23 | Flagged for owner update |
| Loss reason consistency | 0 | Pass |
| Territory reference | 0 | Pass |
| Won land deal without customer flag | 0 | Pass |

## Attach propensity model

A logistic regression on firmographics, workforce mix, platform footprint, customer health, tenure, and incumbent. It is trained only on accounts in specialist-covered territories, where the SASE motion has been fully expressed, so the score means: how likely is this account to be a customer under good coverage? Region and coverage are excluded on purpose, because they describe the go-to-market, not the customer.

- Five-fold cross-validated AUC: 0.757 (gradient boosting: 0.734). The simpler model won and is easier to explain, so it is the one used.
- The top decile attaches at 2.28x the average; the top three deciles hold 52% of customers.

## Whitespace and the coverage gap

Land potential is first-year SASE ARR: (mobile users x price per user + branches x price per site) x a land share by segment, using illustrative prices from `pipeline/config.py`. Propensity-weighted whitespace multiplies that by the propensity score. The coverage gap compares modeled attach to actual attach by territory; latent customers are the sum of propensity minus actual customers.

## Win and loss

Raw win rates can mislead when the same sellers who bundle also have better coverage. The SD-WAN effect is re-estimated with a logistic regression of land-deal outcomes on bundle, rival, their interaction, coverage, renewal alignment, partner source, and segment, and reported as counterfactual averages: against Zscaler and Netskope, 22.5% without the bundle versus 42.7% with it.

## Capacity planning

Monthly model for FY27: August and September are actuals; October through July are forecast. Capacity = productivity per ramped specialist x month's share of annual bookings x productive FTE, plus a baseline from uncovered territories. Productive FTE accounts for a linear ramp, monthly attrition, backfills hired after a lead time, and new hires. Win-rate and deal-size levers scale capacity. The web app runs the same math in JavaScript, and `tests/check_app.py` confirms both give the same answer.

Win-rate levers are derived from the deal-level effects: raising the bundle rate in SSE-rival deals from 46% to 75% is worth 2.8 points of blended win rate; raising renewal-timed deals from 28% to 50% is worth 2.3 points.

## Prisma Browser ICP

A points scorecard from the lift of pre-relaunch adopters over the base, by attribute. It is validated out-of-time on deals created after the March 23, 2026 relaunch.

## Real public data (Market context)

The Market context module is the only part of the project built on real data. It has two inputs, kept apart on purpose:

- `data/curated/`: competitor ARR and Dell'Oro market figures transcribed by hand from public earnings releases and press releases. Every row carries its source URL; verify rows before quoting them. Companies define ARR differently (Zscaler and Netskope report company-wide ARR; Palo Alto Networks and Fortinet report SASE-specific figures), so the comparison is about direction and magnitude.
- `data/public/`: machine-fetched datasets written by `pipeline/fetch_public_data.py`: SEC EDGAR company facts, the CISA Known Exploited Vulnerabilities catalog, and Census Statistics of U.S. Businesses. `pipeline/market.py` checks each file against a fixed schema; a missing or malformed file shows as pending in the app instead of drawing bad charts. `tests/test_market.py` exercises every parsing path against fake fixtures.

## Limitations

- Synthetic data. The numbers illustrate the method; they are not estimates of Palo Alto Networks' business.
- The coverage effect in real data could partly reflect how territories were chosen. A staggered coverage pilot is the right test.
- Prices and land shares are illustrative, not Palo Alto Networks pricing.
- Stage history is simplified to the current stage and its entry date.

## Public sources used for calibration and context

- Q4 FY26 revenue of $3.41B (+34% year over year) and Next-Generation Security ARR of $9.10B (+63%). Palo Alto Networks Q4 FY26 earnings release (SEC Form 8-K, Exhibit 99.1): https://www.sec.gov/Archives/edgar/data/1327567/000132756726000019/ex991q426earningsrelease.htm
- SASE bookings grew 40% year over year in FY26, with displacements of legacy incumbents in nearly 100 accounts worth over $400 million in total contract value. Q4 FY26 earnings call transcript (The Globe and Mail): https://www.theglobeandmail.com/investing/markets/stocks/PANW/pressreleases/4501269/palo-alto-networks-panw-q4-2026-earnings-call-transcript/
- SASE ARR of $1.6B, up 40% year over year, at Q3 FY26. Q3 FY26 earnings call highlights (GuruFocus via Yahoo Finance): https://finance.yahoo.com/markets/stocks/articles/palo-alto-networks-inc-panw-050022001.html
- Prisma Browser above 1,500 customers, about 10% of the Global 2000, at Q2 FY26. Futurum Group analysis of Q2 FY26: https://futurumgroup.com/insights/palo-alto-networks-q2-fy-2026-arr-accelerates-as-platform-strategy-scales/
- SASE ARR includes Prisma Access, Prisma SD-WAN, PAN-OS SD-WAN, SaaS Security, and DLP subscriptions. Palo Alto Networks Q1 FY26 earnings presentation: https://investors.paloaltonetworks.com/static-files/7adeb1fd-e842-49b9-8a37-527abdc15659
- Prisma Browser's agentic-AI evolution: LLM-of-choice workspace, AI data boundaries, prompt-injection and agent-hijacking protection, integrated into Prisma SASE (March 23, 2026). Palo Alto Networks press release: https://www.paloaltonetworks.com/company/press/2026/palo-alto-networks-unveils-the-industry-s-most-secure-browser-built-for-agentic-ai
- FY27 guidance: revenue of $14.1B to $14.2B and NGS ARR of $11.075B to $11.175B. Q4 FY26 earnings call highlights (Yahoo Finance): https://finance.yahoo.com/markets/stocks/articles/palo-alto-networks-q4-earnings-000245297.html
