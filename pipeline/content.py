"""
Operating-cadence content, kept as structured data so the web app and the
markdown docs are generated from one source and can never disagree.

Run:  python pipeline/content.py   (writes docs/operating_cadence/*.md)
"""
from __future__ import annotations

import config as C

METRICS = [
    {"metric": "SASE attach rate", "definition": "Share of next-generation firewall accounts that own Prisma Access.",
     "formula": "Accounts with Prisma Access / all NGFW accounts in scope", "source": "accounts",
     "owner": "GTM Strategy", "cadence": "Weekly",
     "caveat": "Counts logos, not seats. Pair with expansion whitespace to see depth."},
    {"metric": "SASE ARR", "definition": "Annualized recurring revenue from Prisma Access, Prisma SD-WAN, and Prisma Browser.",
     "formula": "Sum of sase_arr + browser_arr for active customers", "source": "accounts (billing snapshot)",
     "owner": "Finance", "cadence": "Monthly",
     "caveat": "Company SASE ARR also includes SaaS Security and DLP; this model covers the three products above."},
    {"metric": "Net new SASE bookings", "definition": "ARR of land and expansion deals closed-won in the period.",
     "formula": "Sum of amount where stage = Closed Won and close_date in period", "source": "opportunities",
     "owner": "Sales Ops", "cadence": "Weekly", "caveat": "Browser bookings are tracked separately in the launch scorecard."},
    {"metric": "Land win rate", "definition": "Share of closed first-purchase deals that were won.",
     "formula": "Closed Won land deals / (Closed Won + Closed Lost) land deals, by close date", "source": "opportunities",
     "owner": "GTM Strategy", "cadence": "Monthly", "caveat": "Count-based. Small segments swing; show deal counts next to rates."},
    {"metric": "Dollar win rate", "definition": "Share of closed ARR that was won, land and expansion together.",
     "formula": "Won ARR / closed ARR, by close date", "source": "opportunities",
     "owner": "GTM Strategy", "cadence": "Monthly", "caveat": "Used as the pipeline-to-bookings conversion in planning math."},
    {"metric": "Pipeline coverage", "definition": "Open pipeline closing in a quarter relative to what is still needed that quarter.",
     "formula": "Open ARR with close_date in quarter / (quarter plan - bookings to date)", "source": "opportunities, plan",
     "owner": "Sales Ops", "cadence": "Weekly",
     "caveat": "Placeholder close dates inflate far-out quarters and deflate near ones. Read current and next quarter first."},
    {"metric": "Quarter-to-date pacing", "definition": "Bookings to date against a straight-line share of the quarter plan.",
     "formula": "QTD bookings / (quarter plan x share of quarter elapsed)", "source": "opportunities, plan",
     "owner": "Sales Ops", "cadence": "Weekly",
     "caveat": "Quarters are back-loaded; compare to the same week last year before calling a miss."},
    {"metric": "Pipeline created", "definition": "ARR of land and expansion opportunities created in the period.",
     "formula": "Sum of amount by created_date", "source": "opportunities",
     "owner": "Marketing and Sales", "cadence": "Weekly", "caveat": "Flag weeks more than 1.5 standard deviations below the trailing 8-week average."},
    {"metric": "Stage stall rate", "definition": "Open deals that have sat in their current stage longer than the stage's service level.",
     "formula": "Deals with (as-of date - stage entry date) > SLA / open deals in stage. SLA: Technical Validation 45 days, other stages 30",
     "source": "opportunities", "owner": "Sales Ops", "cadence": "Weekly",
     "caveat": "Stage history is only as good as rep updates; audit the top 20 stalled deals by hand each month."},
    {"metric": "Slipped deals", "definition": "Deals whose close date was pushed during the period.",
     "formula": "Count and ARR of opportunities with last_push_date in period", "source": "opportunities (field history)",
     "owner": "Sales Ops", "cadence": "Weekly", "caveat": "Repeated pushes (3+) are the signal; a single push is normal."},
    {"metric": "Median sales cycle", "definition": "Typical days from creation to close for won first-purchase deals.",
     "formula": "Median of close_date - created_date, won land deals", "source": "opportunities",
     "owner": "GTM Strategy", "cadence": "Quarterly", "caveat": "Use the median; a few multi-year enterprise cycles distort the mean."},
    {"metric": "Attach propensity", "definition": "Modeled probability an account would be a Prisma Access customer under full specialist coverage.",
     "formula": "Logistic look-alike model on firmographics, incumbents, and platform footprint; trained on covered territories only",
     "source": "accounts_scored", "owner": "GTM Strategy (analytics)", "cadence": "Quarterly refresh",
     "caveat": "A ranking tool, not a forecast. Region and coverage are excluded by design."},
    {"metric": "Land potential", "definition": "Estimated first-year SASE ARR for a non-customer.",
     "formula": "(mobile users x price per user + branches x price per site) x land share by segment",
     "source": "accounts, pricing assumptions", "owner": "GTM Strategy", "cadence": "Quarterly",
     "caveat": "Illustrative pricing. Replace with list or realized pricing before use in planning."},
    {"metric": "Propensity-weighted whitespace", "definition": "Land potential discounted by how likely each account is to buy.",
     "formula": "Sum over non-customers of propensity x land potential", "source": "accounts_scored",
     "owner": "GTM Strategy", "cadence": "Quarterly", "caveat": "Not a one-year number; convert with observed annual conversion before quoting as bookings."},
    {"metric": "Coverage gap", "definition": "Customers we would expect under good coverage but do not have.",
     "formula": "Sum of propensity - actual customers, for a group of territories", "source": "accounts_scored",
     "owner": "GTM Strategy", "cadence": "Quarterly", "caveat": "Near zero in covered territories by construction; read it for uncovered ones."},
    {"metric": "Specialist productivity", "definition": "Annual bookings per fully ramped SASE specialist.",
     "formula": "Covered-territory bookings / average ramped specialist FTE (6-month linear ramp)",
     "source": "opportunities, specialists", "owner": "Finance and GTM Strategy", "cadence": "Quarterly",
     "caveat": "Credits all covered-territory bookings to specialists; core sellers contribute too."},
    {"metric": "Prisma Browser ICP score", "definition": "Points-based fit score derived from how early adopters differ from the base.",
     "formula": "Sum of attribute points, where points = 12 x log2(lift), rounded to 5, capped at 30; tiers set by score cutoffs",
     "source": "accounts_scored", "owner": "Product Marketing and GTM Strategy", "cadence": "Monthly during launch",
     "caveat": "Built on a small early-adopter set; re-derive after 100+ post-launch wins."},
    {"metric": "POV starts", "definition": "Deals entering Technical Validation (proof of value) in the period.",
     "formula": "Count of opportunities by pov_start_date", "source": "opportunities",
     "owner": "Systems Engineering leadership", "cadence": "Weekly during launch", "caveat": "The best leading indicator of launch wins 6 to 8 weeks out."},
    {"metric": "Enablement completion", "definition": "Share of field sellers certified on the launch.",
     "formula": "Certified sellers / field headcount, by region", "source": "launch_enablement_weekly",
     "owner": "Field Enablement", "cadence": "Weekly during launch", "caveat": "Certification is necessary, not sufficient; pair with first-meeting rates."},
]

FUNCTIONS = ["Product", "Sales", "Marketing", "Sales Ops", "Finance", "GTM Strategy"]
RACI = [
    ("Weekly business review", "I", "A", "I", "C", "C", "R"),
    ("Forecast call", "", "A", "I", "R", "C", "C"),
    ("Quarterly business review", "C", "A", "C", "C", "C", "R"),
    ("Annual targets and capacity plan", "C", "C", "C", "R", "A", "R"),
    ("Territory design and carving", "I", "A", "I", "R", "C", "R"),
    ("ICP and segmentation refresh", "C", "C", "A", "I", "I", "R"),
    ("Launch readiness scorecard", "A", "C", "R", "C", "I", "R"),
    ("Competitive win/loss program", "A", "C", "R", "C", "I", "R"),
    ("Pricing and packaging input", "A", "C", "C", "I", "C", "C"),
    ("Metric definitions and data quality", "I", "I", "I", "R", "C", "A"),
    ("Pipeline generation programs", "I", "C", "A", "C", "I", "C"),
]

RHYTHM = [
    {"cadence": "Weekly", "items": [
        ("Monday", "Data refresh and quality checks run before any dashboard updates", "Sales Ops"),
        ("Tuesday", "Forecast call: commit, best case, slips, and stalled deals", "Sales leadership"),
        ("Wednesday", "Weekly business review memo to the VP: what moved, what's at risk, asks", "GTM Strategy"),
        ("Friday", "Pipeline creation check against the weekly target, by region", "Marketing and Sales"),
    ]},
    {"cadence": "Monthly", "items": [
        ("Week 1", "Monthly business review: bookings vs plan, attach, whitespace conversion, launch scorecard", "GTM Strategy"),
        ("Week 2", "Win/loss readout with Product Marketing and Competitive Intelligence", "GTM Strategy"),
        ("Week 3", "Territory health: coverage gaps, stalled segments, rebalancing candidates", "Sales Ops"),
    ]},
    {"cadence": "Quarterly", "items": [
        ("Close + 2 weeks", "Quarterly business review with Sales, Product, Marketing, and Finance", "GTM Strategy"),
        ("Close + 3 weeks", "Propensity model and ICP refresh; whitespace re-ranked", "GTM Strategy"),
        ("Close + 4 weeks", "Capacity check: productivity, ramp, attrition vs plan assumptions", "Finance"),
    ]},
]

PLANNING_CALENDAR = [
    ("February", "Top-down targets and market sizing for FY28", "Finance, GTM Strategy"),
    ("March", "Capacity model and hiring plan: productivity, ramp, attrition, lead time", "GTM Strategy, Finance"),
    ("April", "Account scoring refresh and territory design options", "GTM Strategy, Sales Ops"),
    ("May", "Quota setting and compensation alignment for overlay and core sellers", "Sales Ops, Finance"),
    ("June", "Territory assignments and rules of engagement published", "Sales leadership"),
    ("July", "Launch and kickoff enablement; plans loaded into CRM before Aug 1", "Enablement, Sales Ops"),
]

ONBOARDING = """# Analyst onboarding: first 30 days

A new analyst should be able to own a section of the weekly business review by the end of week two
and present an original finding by day 30. This is the plan I would run.

## Week 1: learn the numbers
- Read the metric dictionary end to end; rebuild three metrics from raw tables in SQL and match them to the dashboard.
- Run the full pipeline locally (`python pipeline/run_all.py`) and read the data-quality report.
- Sit in on the forecast call and the WBR; write down every term you did not know.

## Week 2: own a section
- Take the pipeline-creation section of the WBR. Draft it Tuesday, get feedback Wednesday morning, ship Wednesday.
- Pair on one ad hoc request from a regional leader, start to finish.

## Week 3: go deep on one question
- Pick one territory group with a large coverage gap and explain it: data, deal reviews, two conversations with sellers.

## Week 4: present
- Present one finding to the team in five minutes: the answer first, the evidence second, the ask third.

## Review checklist for any analysis
- Is every metric defined the way the dictionary defines it (denominator, date field, filters)?
- Are the sample sizes shown next to the rates?
- Did the data-quality checks pass for the tables used?
- Could the headline be wrong for a boring reason (seasonality, one large deal, a territory change)?
- Is there a clear so-what: what should someone do differently on Monday?
"""


def write_docs():
    out = C.DOCS / "operating_cadence"
    out.mkdir(parents=True, exist_ok=True)

    lines = ["# Metric dictionary", "",
             "One definition per metric. Every chart, memo, and SQL file in this project uses these.", "",
             "| Metric | Definition | Formula | Source | Owner | Cadence | Watch out for |",
             "|---|---|---|---|---|---|---|"]
    for m in METRICS:
        lines.append(f"| {m['metric']} | {m['definition']} | {m['formula']} | {m['source']} | {m['owner']} | "
                     f"{m['cadence']} | {m['caveat']} |")
    (out / "metric_dictionary.md").write_text("\n".join(lines) + "\n")

    lines = ["# RACI: SASE go-to-market operating model", "",
             "R = responsible, A = accountable (exactly one per row), C = consulted, I = informed.", "",
             "| Activity | " + " | ".join(FUNCTIONS) + " |", "|---|" + "---|" * len(FUNCTIONS)]
    for row in RACI:
        assert row[1:].count("A") == 1, f"RACI row needs exactly one A: {row[0]}"
        lines.append(f"| {row[0]} | " + " | ".join(x or "-" for x in row[1:]) + " |")
    (out / "raci.md").write_text("\n".join(lines) + "\n")

    lines = ["# Operating rhythm and FY28 planning calendar", "",
             "Palo Alto Networks' fiscal year starts August 1, so FY28 planning runs February through July 2027.", ""]
    for block in RHYTHM:
        lines += [f"## {block['cadence']}", "", "| When | What | Owner |", "|---|---|---|"]
        lines += [f"| {w} | {what} | {o} |" for w, what, o in block["items"]]
        lines.append("")
    lines += ["## Annual planning (FY28)", "", "| Month | Milestone | Owners |", "|---|---|---|"]
    lines += [f"| {m} | {what} | {o} |" for m, what, o in PLANNING_CALENDAR]
    (out / "operating_calendar.md").write_text("\n".join(lines) + "\n")

    (out / "analyst_onboarding.md").write_text(ONBOARDING)

    wbr = """# Weekly business review template

Sent Wednesday. One page. The first three lines should be enough for a VP who reads nothing else.

**Subject:** SASE WBR, week {n} of {quarter}: {headline}

**Headline (one sentence):** where the quarter stands and the single most important thing that changed.

**Numbers**
- Bookings this week and quarter to date, against plan and against straight-line pace
- Pipeline created this week against the trailing 8-week average (flag if more than 1.5 SD below)
- Coverage for the rest of this quarter and for next quarter

**What moved:** top wins, notable losses (with reason), deals that slipped (count, ARR, repeat slippers).

**Risks:** the three largest open deals closing this quarter that are stalled or slipping, with owner and next step.

**Asks:** specific requests with an owner and a date. If there are no asks, say so.

**Hygiene:** open deals with past-due close dates, missing loss reasons, and anything the data-quality checks flagged.

The web app's Executive layer drafts this automatically for any week; the analyst edits, it does not replace judgment.
"""
    (out / "wbr_template.md").write_text(wbr)
    print(f"wrote operating cadence docs to {out}")


if __name__ == "__main__":
    write_docs()
