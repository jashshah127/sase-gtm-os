"""
Writes the Prisma Browser field launch kit and the methodology document.
Data-driven sections pull from the pipeline outputs so the numbers always match.

Writes docs/launch_kit/*.md and docs/methodology.md
"""
from __future__ import annotations

import json

import config as C

SOURCES = [
    ("Q4 FY26 revenue of $3.41B (+34% year over year) and Next-Generation Security ARR of $9.10B (+63%)",
     "Palo Alto Networks Q4 FY26 earnings release (SEC Form 8-K, Exhibit 99.1)",
     "https://www.sec.gov/Archives/edgar/data/1327567/000132756726000019/ex991q426earningsrelease.htm"),
    ("SASE bookings grew 40% year over year in FY26, with displacements of legacy incumbents in nearly 100 accounts worth over $400 million in total contract value",
     "Q4 FY26 earnings call transcript (The Globe and Mail)",
     "https://www.theglobeandmail.com/investing/markets/stocks/PANW/pressreleases/4501269/palo-alto-networks-panw-q4-2026-earnings-call-transcript/"),
    ("SASE ARR of $1.6B, up 40% year over year, at Q3 FY26",
     "Q3 FY26 earnings call highlights (GuruFocus via Yahoo Finance)",
     "https://finance.yahoo.com/markets/stocks/articles/palo-alto-networks-inc-panw-050022001.html"),
    ("Prisma Browser above 1,500 customers, about 10% of the Global 2000, at Q2 FY26",
     "Futurum Group analysis of Q2 FY26",
     "https://futurumgroup.com/insights/palo-alto-networks-q2-fy-2026-arr-accelerates-as-platform-strategy-scales/"),
    ("SASE ARR includes Prisma Access, Prisma SD-WAN, PAN-OS SD-WAN, SaaS Security, and DLP subscriptions",
     "Palo Alto Networks Q1 FY26 earnings presentation",
     "https://investors.paloaltonetworks.com/static-files/7adeb1fd-e842-49b9-8a37-527abdc15659"),
    ("Prisma Browser's agentic-AI evolution: LLM-of-choice workspace, AI data boundaries, prompt-injection and agent-hijacking protection, integrated into Prisma SASE (March 23, 2026)",
     "Palo Alto Networks press release",
     "https://www.paloaltonetworks.com/company/press/2026/palo-alto-networks-unveils-the-industry-s-most-secure-browser-built-for-agentic-ai"),
    ("FY27 guidance: revenue of $14.1B to $14.2B and NGS ARR of $11.075B to $11.175B",
     "Q4 FY26 earnings call highlights (Yahoo Finance)",
     "https://finance.yahoo.com/markets/stocks/articles/palo-alto-networks-q4-earnings-000245297.html"),
]


def pct(v, d=0):
    return f"{v * 100:.{d}f}%"


def money(v):
    return f"${v / 1e6:.1f}M" if v >= 1e6 else f"${v / 1e3:.0f}K"


def icp_doc(model):
    icp = model["icp"]
    rows = sorted([r for r in icp["table"] if r["points"] > 0], key=lambda r: -r["lift"])
    tiers = {t["tier"]: t for t in icp["tiers"]}
    a, c = tiers["A"], tiers["C"]
    lines = [
        "# Prisma Browser: ideal customer profile",
        "",
        "*Derived from the synthetic dataset in this project. Replace with CRM data before field use.*",
        "",
        "## Who buys first",
        "",
        f"Early Prisma Browser adopters ({icp['early_adopters']} accounts that bought before the March 2026 relaunch) "
        "differ from the firewall base in consistent ways. The strongest signals, in order of lift:",
        "",
        "| Attribute | Value | Share of base | Share of early adopters | Lift | ICP points |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows[:12]:
        lines.append(f"| {r['attribute']} | {r['value']} | {pct(r['base_share'], 1)} | {pct(r['adopter_share'], 1)} | "
                     f"{r['lift']:.2f}x | {r['points']} |")
    lines += [
        "",
        "In plain terms: the buyer has a large contractor or third-party workforce, many unmanaged devices, "
        "often a VDI estate that exists mainly to give those users browser access, and usually already runs "
        "Prisma Access. Regulated and knowledge-work industries lead.",
        "",
        "## Tiers",
        "",
        f"Points come from lift (12 x log2 of lift, rounded to 5, capped at 30). Tier A is a score of "
        f"{icp['tier_cutoffs']['A']} or more; Tier B is {icp['tier_cutoffs']['B']} or more.",
        "",
        "| Tier | Accounts | Early adoption rate | Post-launch opps per 100 accounts | Post-launch win rate |",
        "|---|---|---|---|---|",
    ]
    for t in icp["tiers"]:
        wr = pct(t["post_launch_win_rate"]) if t["post_launch_win_rate"] is not None else "n/a"
        lines.append(f"| {t['tier']} | {t['accounts']:,} | {pct(t['early_adopter_rate'], 1)} | "
                     f"{t['opps_per_100_accounts']} | {wr} |")
    lines += [
        "",
        "## Does it hold up?",
        "",
        f"The scorecard was built only from pre-relaunch adopters, then checked against deals created after "
        f"March 23, 2026. Tier A generated {a['opps_per_100_accounts']} opportunities per 100 accounts against "
        f"{c['opps_per_100_accounts']} for Tier C, and won {a['post_launch_wins']} of the "
        f"{sum(t['post_launch_wins'] for t in icp['tiers'])} post-launch deals. That out-of-time check is what makes "
        "the ICP usable for routing, not just descriptive.",
        "",
        "## How to use it",
        "",
        "- Tier A: route to SASE specialists and SEs for a proactive POV offer; lead with the contractor or VDI use case.",
        "- Tier B: partner-led and marketing programs; qualify on contractor volume and AI usage policy first.",
        "- Tier C: nurture. Do not spend SE time without a named use case.",
        "- Refresh the points after 100 or more post-launch wins; early-adopter samples are small.",
        "",
        "## Watch-outs",
        "",
        "- A fully managed device fleet with few contractors is a weak fit even in a strong industry.",
        "- VDI signals are strongest where VDI exists mainly for browser-based apps; heavy desktop-app VDI is a different sale.",
        "",
    ]
    return "\n".join(lines)


POSITIONING = """# Prisma Browser: positioning one-pager

*Working draft for Product Marketing review. Capability statements are limited to what Palo Alto Networks has
announced publicly (see sources). Anything else is a hypothesis to validate.*

## Positioning statement

**For** security and IT leaders at enterprises with large contractor, third-party, or unmanaged-device populations,
**who** need to give those users safe access to SaaS, private apps, and now AI tools without shipping laptops or
maintaining VDI, **Prisma Browser** is a secure enterprise browser that is part of Prisma SASE. **Unlike** consumer
browsers with extensions, standalone enterprise browsers, or VDI kept alive for browser apps, it applies the same
zero trust and data policies customers already run in Prisma Access, and extends them to AI agents working in the
browser.

## Why now

- The browser is where work happens. Palo Alto Networks cites 85% of the workday spent in the browser.
- AI is moving from a tool to an actor. Agents now browse, fill forms, and move data on a user's behalf, which creates
  new paths for data leakage and new attacks such as prompt injection hidden in web pages.
- Contractor and BYOD access is still expensive. Many VDI estates exist mostly to deliver browser-based apps.

## Messaging pillars

**Secure work on any device.** Give contractors, partners, and BYOD users a managed, policy-controlled workspace
without a managed laptop.

**Retire VDI where it only serves the browser.** Move browser-app users off virtual desktops and redirect that spend.
(Hypothesis to size per customer with a VDI cost worksheet.)

**Govern AI inside the browser.** Per the March 2026 announcement: discover user AI activity, enforce content-aware
boundaries so agents stay in scope, keep sensitive data out of unmanaged or public AI tools, and block prompt-injection
attempts designed to hijack agents.

**One platform, one policy.** Integrated into Prisma SASE, so browser controls follow the policies security teams
already manage.

## Proof points (public)

- More than 1,500 Prisma Browser customers, about 10% of the Global 2000, as of Q2 FY26 (analyst coverage).
- Agentic-AI evolution announced March 23, 2026, including LLM-of-choice support.
- Part of Prisma SASE, whose ARR reached $1.6B, up 40% year over year, at Q3 FY26.

## Proof we still need to build

- Two reference customers per use case: contractor access, VDI replacement, AI governance.
- A VDI cost-comparison worksheet the field can fill in during discovery.
- POV success criteria that finish in 30 days (see the discovery guide).
"""

BATTLECARD = """# Prisma Browser: competitive battlecard

*Hypotheses for Competitive Intelligence to validate. Competitor descriptions reflect their public positioning at a
high level; nothing here is a verified claim about a competitor's product. Keep this card factual and never
disparaging in customer conversations.*

## The real competitor is usually the status quo

**What it looks like:** VDI or desktop-as-a-service for contractors and BYOD users, plus a consumer browser with
extensions for everyone else.

**Where it's strong:** already paid for, familiar to IT, covers desktop apps as well as browser apps.

**How we think we win:** separate browser-only users from desktop-app users. For the browser-only group, compare the
cost and user experience of a virtual desktop against a secure browser, and show that AI-era controls (agent scope,
data boundaries, prompt-injection blocking) do not exist in the status quo.

**Questions that open it up:**
- How many of your VDI users only need browser-based apps?
- What does a contractor seat cost you per year, all in?
- How do you control what an AI agent can do in a browser session today?

## Standalone enterprise browsers

**Where they're strong:** a focused product and a head start in the category's early conversations.

**How we think we win:** platform integration. If the customer already runs Prisma Access, browser policy can build on
the policies they already manage instead of adding another console and policy model.

**Questions:** Who will own browser policy, and how will it stay consistent with your SASE and data-protection policy?
What happens to that policy when users leave the browser for other apps?

## Browser vendors' own enterprise management

**Where they're strong:** deployment is simple and the browser is often already installed.

**How we think we win:** depth of security and data controls, especially for unmanaged devices and third parties, and
consistency with network-level SASE policy. Validate specific gaps with CI before using them.

## SSE vendors' browser offerings (for example Zscaler and Netskope)

**Where they're strong:** incumbency in SSE accounts and existing relationships with the security team.

**How we think we win:** pair the browser with the single-vendor SASE story (SD-WAN plus SSE plus browser). In this
project's win/loss data, bundling SD-WAN lifts win rates against SSE-only rivals sharply; the browser can extend that
platform argument. Treat as a hypothesis until confirmed with real win/loss reviews.

## Landmines to avoid

- Do not promise VDI savings before you know how many users are browser-only.
- Do not claim capabilities beyond what has been announced publicly or confirmed by Product.
- Do not lead with AI governance when the buyer's pain is contractor onboarding; lead with their pain, then expand.
"""

DISCOVERY = """# Prisma Browser: discovery and POV guide

The goal of discovery is to find a named use case with a number attached (users, seats, cost, or risk) and a buyer who
owns it. The goal of a POV is to prove that use case in 30 days.

## Questions by persona

**CISO or security leader**
- Which users can reach sensitive apps from devices you do not manage? How many?
- How are you controlling what employees and AI agents can paste, upload, or send to AI tools?
- Where would a browser-level control have stopped your last data incident?

**End-user computing or VDI owner**
- How many virtual desktops exist mainly so people can use browser-based apps?
- What is your all-in cost per VDI seat, and when does the next renewal or hardware refresh land?
- How long does it take to onboard a contractor today, from contract signature to first productive login?

**Third-party risk or procurement**
- How many contractors, agencies, and partners access internal apps? How often do they turn over?
- What do your contracts require for device security and data handling?

**AI or innovation leader**
- Which AI tools and agents are sanctioned today, and how do you enforce that?
- What would you let an agent do in a browser if you could scope and audit it?

## Qualification

A qualified opportunity has all four:
1. A use case with a population of at least a few hundred users (contractors, BYOD, or VDI browser-only).
2. A named owner with budget or a VDI renewal within 12 months.
3. An existing Prisma Access footprint, or an active SASE evaluation.
4. Agreement to a POV with written success criteria.

## POV success criteria (30 days)

| Criterion | Target | How we measure it |
|---|---|---|
| Time to first protected session | Under 1 day | Deployment log |
| Users onboarded | At least 100 in the target group | Admin console |
| Policy parity | Key data controls match current policy | Side-by-side test plan |
| User experience | Satisfaction at or above the current tool | Short survey at day 21 |
| Business case | VDI seats or contractor laptops that could be retired | Customer-validated worksheet |

## Red flags

- No owner for the contractor or VDI population.
- The POV has no end date or no written success criteria.
- The only driver is a checkbox for an RFP.
"""


def scorecard_doc(launch):
    lines = [
        "# Prisma Browser: launch scorecard",
        "",
        f"Tracked weekly since the March 23, 2026 relaunch. Status as of {C.AS_OF:%B %d, %Y}. "
        "The plan curves are synthetic, as is all data in this project.",
        "",
        "| Metric | Actual | Plan to date | Attainment | Status |",
        "|---|---|---|---|---|",
    ]
    for l in launch["lines"]:
        if l["metric"] == "Pipeline created":
            a, p = money(l["actual"]), money(l["plan"])
        elif l["metric"].startswith("Field certified"):
            a, p = pct(l["actual"]), pct(l["plan"])
        else:
            a, p = f"{l['actual']:,.0f}", f"{l['plan']:,.0f}"
        lines.append(f"| {l['metric']} | {a} | {p} | {pct(l['attainment'])} | {l['status']} |")
    t = launch["totals"]
    lines += [
        "",
        f"Post-relaunch totals: {t['opps']} opportunities, {money(t['pipeline'])} of pipeline, {t['wins']} wins worth "
        f"{money(t['win_arr'])}, a {pct(t['win_rate'])} win rate on closed deals, and {pct(t['lost_at_pov_share'])} "
        "of losses happening at the POV stage.",
        "",
        "## Reading it",
        "",
        "Pipeline and wins are close to plan. POV starts are the constraint: fewer deals are reaching proof of value "
        "than planned, and most losses happen there. JAPAC certification lags the 80% target.",
        "",
        "## Decision rules",
        "",
        "- POV starts below 85% of plan for three straight weeks: add SE capacity or a packaged 30-day POV kit.",
        "- A region below 70% certification at week 12: targeted enablement sprint and manager sign-off.",
        "- Tier A share of new pipeline below 50%: tighten routing to the ICP.",
        "",
        "## Metric definitions",
        "",
        "| Metric | Definition | Owner |",
        "|---|---|---|",
        "| Pipeline created | ARR of Browser opportunities created since relaunch | Marketing and Sales |",
        "| POVs started | Browser deals entering Technical Validation | SE leadership |",
        "| Deals won | Browser deals closed-won since relaunch | Sales |",
        "| Field certified | Certified sellers / field headcount, by region | Field Enablement |",
        "",
    ]
    return "\n".join(lines)


def methodology_doc(summary, model, quality, planning):
    de = summary["deal_effects"]
    lines = [
        "# Methodology",
        "",
        "This project is an independent, working model of the SASE Product GTM Manager role. Every account, deal, and "
        "seller in it is synthetic. Public Palo Alto Networks figures are used only to calibrate scale and growth, and "
        "are cited below. Nothing here is affiliated with or endorsed by Palo Alto Networks.",
        "",
        "## Why synthetic data, and how it is kept honest",
        "",
        "Real CRM data is confidential, so the data is simulated. The risk with simulated data is that an analysis just "
        "finds what was planted. Two safeguards: every planted pattern is disclosed below, and the analysis uses methods "
        "that would work unchanged on a real Salesforce export (the SQL in `sql/` targets BigQuery).",
        "",
        "## Data model",
        "",
        "| Table | Grain | Key fields |",
        "|---|---|---|",
        "| accounts | One firewall customer | segment, region, industry, territory, employees, branches, remote and contractor share, unmanaged devices, VDI, incumbent remote access, firewall renewal, Prisma products owned, SASE ARR |",
        "| opportunities | One deal | type (land, expansion, browser), product, created and close dates, stage, amount, competitor, SD-WAN bundle, source, loss reason and stage, stage entry date, pushes, renewal alignment, POV start |",
        "| territories | One core territory | region, segment, account count, SASE specialist coverage |",
        "| specialists | One SASE overlay specialist | region, segment, hire date |",
        "| launch_enablement_weekly | Region by week | field headcount, certified share |",
        "",
        "## How the data is generated",
        "",
        f"{summary['accounts']:,} firewall accounts are simulated quarter by quarter from FY23 Q3, using Palo Alto "
        "Networks' fiscal calendar (the fiscal year starts August 1). The dataset is frozen at September 25, 2026, "
        "week 8 of FY27 Q1. Each quarter, non-customers may open a land opportunity; its probability rises with the "
        "account's fit and with specialist coverage, and grows over time. Deals carry a competitor, an SD-WAN bundle "
        "decision, a source, a cycle length, and a win probability; they then move through stages, sometimes slip, and "
        "close. Customers generate expansion deals. Prisma Browser has early adopters before the relaunch and weekly "
        "pipeline after it.",
        "",
        "### Planted patterns (disclosed so nothing is found by accident)",
        "",
        "- Fit: larger segments, remote-heavy and contractor-heavy workforces, bigger branch footprints, Cortex ownership, "
        "and GlobalProtect VPN users are likelier to adopt. SSE incumbents (Zscaler, Netskope, and others) are much less likely.",
        "- Coverage: territories with a SASE specialist create more opportunities and win more often. Coverage is thin in "
        "EMEA and JAPAC mid-market and commercial by design.",
        "- Competition: win rates are lower against Zscaler and Netskope, and an SD-WAN bundle recovers a large part of "
        "that gap. The bundle helps only a little against other rivals.",
        "- Timing: deals opened 90 to 270 days before the firewall renewal win more often.",
        "- Partners: partner-sourced deals win more often in mid-market and commercial.",
        "- Process: some deals stall in Technical Validation; some open deals carry placeholder close dates in later quarters.",
        "- Browser: adoption rises with contractor share, unmanaged devices, VDI, industry, and existing Prisma Access.",
        "- Competitor names are real so the analysis reads realistically. The win rates are synthetic and say nothing about "
        "any vendor's actual performance.",
        "",
        "### Calibration to public figures",
        "",
        f"The simulation was tuned so the book looks like a plausible slice of the business: attach of "
        f"{pct(summary['attach_rate'], 1)}, FY26 SASE bookings growth of {pct(summary['fy26_growth'], 1)} (Palo Alto "
        f"Networks reported 40% SASE bookings growth in FY26), and a land win rate of {pct(summary['fy26_land_win_rate'], 1)}.",
        "",
        "## Data quality",
        "",
        f"Known issues are injected into the raw export, and `pipeline/validate.py` must catch every one before anything "
        f"downstream runs. {quality['quarantined_opportunities']} opportunities were quarantined and duplicate accounts "
        "merged; past-due close dates are flagged for owners. The run fails if any injected issue is missed.",
        "",
        "| Check | Rows failed | Action |",
        "|---|---|---|",
    ]
    lines += [f"| {c['check']} | {c['rows_failed']} | {c['action']} |" for c in quality["checks"]]
    m = model["model"]
    lines += [
        "",
        "## Attach propensity model",
        "",
        "A logistic regression on firmographics, workforce mix, platform footprint, customer health, tenure, and incumbent. "
        "It is trained only on accounts in specialist-covered territories, where the SASE motion has been fully expressed, "
        "so the score means: how likely is this account to be a customer under good coverage? Region and coverage are "
        "excluded on purpose, because they describe the go-to-market, not the customer.",
        "",
        f"- Five-fold cross-validated AUC: {m['cv_auc_logistic']:.3f} (gradient boosting: {m['cv_auc_gradient_boosting']:.3f}). "
        "The simpler model won and is easier to explain, so it is the one used.",
        f"- The top decile attaches at {m['top_decile_lift']}x the average; the top three deciles hold "
        f"{pct(m['top3_decile_capture'])} of customers.",
        "",
        "## Whitespace and the coverage gap",
        "",
        "Land potential is first-year SASE ARR: (mobile users x price per user + branches x price per site) x a land share "
        "by segment, using illustrative prices from `pipeline/config.py`. Propensity-weighted whitespace multiplies that by "
        "the propensity score. The coverage gap compares modeled attach to actual attach by territory; latent customers are "
        "the sum of propensity minus actual customers.",
        "",
        "## Win and loss",
        "",
        "Raw win rates can mislead when the same sellers who bundle also have better coverage. The SD-WAN effect is "
        "re-estimated with a logistic regression of land-deal outcomes on bundle, rival, their interaction, coverage, "
        "renewal alignment, partner source, and segment, and reported as counterfactual averages: against Zscaler and "
        f"Netskope, {pct(de['adj_win_sse_no_bundle'], 1)} without the bundle versus {pct(de['adj_win_sse_bundle'], 1)} with it.",
        "",
        "## Capacity planning",
        "",
        "Monthly model for FY27: August and September are actuals; October through July are forecast. Capacity = "
        "productivity per ramped specialist x month's share of annual bookings x productive FTE, plus a baseline from "
        "uncovered territories. Productive FTE accounts for a linear ramp, monthly attrition, backfills hired after a lead "
        "time, and new hires. Win-rate and deal-size levers scale capacity. The web app runs the same math in JavaScript, "
        "and `tests/check_app.py` confirms both give the same answer.",
        "",
        f"Win-rate levers are derived from the deal-level effects: raising the bundle rate in SSE-rival deals from "
        f"{pct(planning['levers']['bundle_share_in_sse_now'])} to {pct(planning['levers']['bundle_share_target'])} is worth "
        f"{planning['levers']['bundle_pts']} points of blended win rate; raising renewal-timed deals from "
        f"{pct(planning['levers']['aligned_share_now'])} to {pct(planning['levers']['aligned_share_target'])} is worth "
        f"{planning['levers']['renewal_pts']} points.",
        "",
        "## Prisma Browser ICP",
        "",
        "A points scorecard from the lift of pre-relaunch adopters over the base, by attribute. It is validated "
        "out-of-time on deals created after the March 23, 2026 relaunch.",
        "",
        "## Real public data (Market context)",
        "",
        "The Market context module is the only part of the project built on real data. It has two inputs, kept apart on purpose:",
        "",
        "- `data/curated/`: competitor ARR and Dell'Oro market figures transcribed by hand from public earnings releases and "
        "press releases. Every row carries its source URL; verify rows before quoting them. Companies define ARR differently "
        "(Zscaler and Netskope report company-wide ARR; Palo Alto Networks and Fortinet report SASE-specific figures), so the "
        "comparison is about direction and magnitude.",
        "- `data/public/`: machine-fetched datasets written by `pipeline/fetch_public_data.py`: SEC EDGAR company facts, the "
        "CISA Known Exploited Vulnerabilities catalog, and Census Statistics of U.S. Businesses. `pipeline/market.py` checks each "
        "file against a fixed schema; a missing or malformed file shows as pending in the app instead of drawing bad charts. "
        "`tests/test_market.py` exercises every parsing path against fake fixtures.",
        "",
        "## Limitations",
        "",
        "- Synthetic data. The numbers illustrate the method; they are not estimates of Palo Alto Networks' business.",
        "- The coverage effect in real data could partly reflect how territories were chosen. A staggered coverage pilot is "
        "the right test.",
        "- Prices and land shares are illustrative, not Palo Alto Networks pricing.",
        "- Stage history is simplified to the current stage and its entry date.",
        "",
        "## Public sources used for calibration and context",
        "",
    ]
    lines += [f"- {fact}. {src}: {url}" for fact, src, url in SOURCES]
    lines.append("")
    return "\n".join(lines)


def main():
    summary = json.loads((C.DATA_PROCESSED / "summary.json").read_text())
    model = json.loads((C.DATA_PROCESSED / "model_report.json").read_text())
    quality = json.loads((C.DATA_PROCESSED / "quality_report.json").read_text())
    planning = json.loads((C.DATA_PROCESSED / "planning.json").read_text())
    launch = json.loads((C.DATA_PROCESSED / "launch_scorecard.json").read_text())
    kit = C.DOCS / "launch_kit"
    kit.mkdir(parents=True, exist_ok=True)
    (kit / "01_icp.md").write_text(icp_doc(model))
    (kit / "02_positioning.md").write_text(POSITIONING)
    (kit / "03_battlecard.md").write_text(BATTLECARD)
    (kit / "04_discovery_guide.md").write_text(DISCOVERY)
    (kit / "05_launch_scorecard.md").write_text(scorecard_doc(launch))
    (C.DOCS / "methodology.md").write_text(methodology_doc(summary, model, quality, planning))
    print("wrote launch kit (5 docs) and methodology.md")


if __name__ == "__main__":
    main()
