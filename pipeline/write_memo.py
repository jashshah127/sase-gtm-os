"""
Flagship executive memo, generated from the pipeline's own outputs so every
number in it matches the data and the web app.

Writes docs/executive_memo.md and docs/executive_memo.pdf (one page, verified).
"""
from __future__ import annotations

import json

import pandas as pd
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (KeepTogether, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

import config as C

INK, ULTRA, SLATE, HAZE = HexColor("#0F1B33"), HexColor("#2B3FE0"), HexColor("#5B6B84"), HexColor("#DCE2EC")


def m(v):  # money
    return f"${v / 1e6:.1f}M" if abs(v) >= 1e6 else f"${v / 1e3:.0f}K"


def pct(v, d=0):
    return f"{v * 100:.{d}f}%"


def weekly_pipeline_avg():
    opp = pd.read_csv(C.DATA_CLEAN / "opportunities.csv", parse_dates=["created_date"])
    core = opp[opp.opp_type.isin(["Land", "Expansion"])]
    end = pd.Timestamp(C.AS_OF)
    recent = core[(core.created_date > end - pd.Timedelta(days=56)) & (core.created_date <= end)]
    return float(recent.amount.sum() / 8)


def build():
    s = json.loads((C.DATA_PROCESSED / "summary.json").read_text())
    p = json.loads((C.DATA_PROCESSED / "planning.json").read_text())
    ln = json.loads((C.DATA_PROCESSED / "launch_scorecard.json").read_text())
    unc = next(g for g in s["coverage_gap"]["by_coverage"] if g["covered"] == 0)
    de, lev, ws = s["deal_effects"], p["levers"], s["whitespace"]
    rec = next(x for x in p["scenarios"] if x["name"].startswith("Recommended"))
    hire_only = next(x for x in p["scenarios"] if x["name"] == "Hiring only")
    plays = next(x for x in p["scenarios"] if x["name"] == "Win-rate plays")
    q2 = s["pipeline_coverage"][1]
    wk = weekly_pipeline_avg()
    rec_hires = rec["params"]["hires_now"]
    q = json.loads((C.DATA_PROCESSED / "quality_report.json").read_text())
    pov = next(l for l in ln["lines"] if l["metric"] == "POVs started")
    japac = next(l for l in ln["lines"] if l["metric"] == "Field certified, JAPAC")

    memo = {
        "to": "VP, SASE Go-to-Market",
        "from": "Jash Shah, SASE Product GTM (independent portfolio exercise)",
        "date": "September 25, 2026 (week 8 of FY27 Q1)",
        "subject": "Closing the FY27 SASE gap with coverage, timing, and the SD-WAN bundle",
        "bottom_line": (
            f"FY27 needs {m(s['fy27_target'])} in SASE bookings, 35% above FY26's {m(s['fy26_bookings'])}. "
            f"Current capacity reaches about {pct(p['baseline']['attainment'])} of that. Two win-rate plays close most of "
            f"the gap at no headcount cost, and {rec_hires} specialist hires in uncovered mid-market territories close the rest. "
            f"Q1 is ahead of pace; Q2 pipeline is the near-term risk."),
        "sections": [
            {"title": "What the data shows", "bullets": [
                ("The whitespace is concentrated and under-covered.",
                 f"{ws['non_customers']:,} firewall accounts do not own Prisma Access. Propensity-weighted whitespace is "
                 f"{m(ws['expected_value_total'])}, and half of it sits in {ws['accounts_for_half_of_ev']} accounts. Territories "
                 f"without a SASE specialist attach at {pct(unc['actual_attach'], 1)} against a modeled {pct(unc['modeled_attach'], 1)}: "
                 f"about {unc['latent_customers']} customers we would expect and do not have, concentrated in JAPAC and EMEA "
                 f"mid-market and commercial. This is a coverage problem, not a demand problem."),
                ("The SD-WAN bundle wins competitive deals.",
                 f"Against Zscaler and Netskope, deals that include SD-WAN win {pct(de['adj_win_sse_bundle'])} versus "
                 f"{pct(de['adj_win_sse_no_bundle'])} without it, and the gap holds after controlling for coverage, segment, renewal "
                 f"timing, and source. Only {pct(lev['bundle_share_in_sse_now'])} of those deals include SD-WAN today."),
                ("Timing matters.",
                 f"Deals opened 90 to 270 days before the firewall renewal win {pct(de['adj_win_aligned'])} versus "
                 f"{pct(de['adj_win_not_aligned'])}. Only {pct(lev['aligned_share_now'])} of land deals are timed that way."),
                ("Q2 is the risk, not Q1.",
                 f"Q1 is pacing {pct(s['q1_pacing'])} of plan, but pipeline closing in Q2 covers {q2['coverage']:.2f}x of Q2's "
                 f"{m(s['fy27_plan_by_quarter'][1])} plan."),
            ]},
            {"title": "Recommendations", "bullets": [
                ("Make SD-WAN the default in every Zscaler and Netskope deal.",
                 f"Target a {pct(lev['bundle_share_target'])} bundle rate (from {pct(lev['bundle_share_in_sse_now'])}). "
                 f"Owners: Product Marketing and Sales. Worth about {lev['bundle_pts']} points of blended win rate."),
                ("Run a renewal-timed attach play.",
                 f"Every account renewing its firewall in 90 to 270 days gets a SASE motion; target {pct(lev['aligned_share_target'])} "
                 f"of land deals (from {pct(lev['aligned_share_now'])}). Owners: GTM Strategy and Sales Ops. Worth about "
                 f"{lev['renewal_pts']} points."),
                (f"Approve {rec_hires} SASE specialists now for JAPAC and EMEA mid-market.",
                 f"About {m(rec['new_hire_cost_fy27'])} in FY27 cost for {m(rec['new_hire_run_rate'])} of annual capacity once ramped. "
                 f"Hiring alone would take {hire_only['params']['hires_now']} specialists and {m(hire_only['new_hire_cost_fy27'])}."),
                ("Start a Q2 pipeline sprint with Marketing and Partners.",
                 f"Lift weekly pipeline creation from {m(wk)} to {m(wk + 1e6)} through mid-November, prioritizing "
                 f"mid-market and commercial deals short enough to close inside Q2."),
            ]},
            {"title": "Expected impact", "paragraph": (
                f"The two plays alone move modeled FY27 attainment from {pct(p['baseline']['attainment'])} to "
                f"{pct(plays['attainment'])}. With {rec_hires} hires it reaches {pct(rec['attainment'])}, about "
                f"{m(rec['incremental_vs_current'])} above the current path. On the Prisma Browser launch, POV starts are at "
                f"{pct(pov['attainment'])} of plan and JAPAC certification is at {pct(japac['actual'])}; I would add SE capacity "
                f"for POVs before adding more top-of-funnel spend.")},
            {"title": "Risks and what would change my mind", "bullets": [
                ("Selection, not coverage.",
                 "Covered territories may have been chosen because they were stronger. The clean test is a pilot: add coverage "
                 "to half of the eligible uncovered territories and compare attach after two quarters."),
                ("Comp and channel conflict.",
                 "Overlay specialists double-credit core sellers and can crowd partners; rules of engagement come before hiring."),
                ("Ramp and discounting.",
                 "If hiring lead time slips past five months, hires add little in FY27 and the plays carry more weight. "
                 "Watch bundle discounting so win-rate gains do not come out of deal size."),
            ]},
        ],
        "method": (
            f"Method: synthetic book of {s['accounts']:,} firewall accounts and {q['clean_opportunities']:,} validated opportunities "
            f"({q['quarantined_opportunities']} quarantined by automated checks); logistic look-alike model (cross-validated AUC {s['model']['cv_auc_logistic']:.2f}) trained on "
            f"specialist-covered territories; capacity model with ramp, attrition, and backfills. All data is synthetic and "
            f"illustrative. Not affiliated with or endorsed by Palo Alto Networks."),
    }
    return memo


def to_markdown(memo) -> str:
    out = ["# Memo", "",
           f"**To:** {memo['to']}  ", f"**From:** {memo['from']}  ", f"**Date:** {memo['date']}  ",
           f"**Subject:** {memo['subject']}", "", f"**Bottom line.** {memo['bottom_line']}", ""]
    for sec in memo["sections"]:
        out += [f"## {sec['title']}", ""]
        if "paragraph" in sec:
            out += [sec["paragraph"], ""]
        for lead, text in sec.get("bullets", []):
            out.append(f"- **{lead}** {text}")
        if sec.get("bullets"):
            out.append("")
    out += [f"*{memo['method']}*", ""]
    return "\n".join(out)


def to_pdf(memo, path, base_size=10.0):
    for size in [base_size - 0.2 * k for k in range(8)]:
        doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=0.62 * inch, rightMargin=0.62 * inch,
                                topMargin=0.5 * inch, bottomMargin=0.45 * inch,
                                title="SASE GTM memo", author="Jash Shah")
        body = ParagraphStyle("body", fontName="Helvetica", fontSize=size, leading=size * 1.32, textColor=INK,
                              alignment=TA_LEFT)
        small = ParagraphStyle("small", parent=body, fontSize=size - 1.3, leading=(size - 1.3) * 1.3, textColor=SLATE)
        h1 = ParagraphStyle("h1", parent=body, fontName="Helvetica-Bold", fontSize=size + 6.5, leading=size + 9)
        h2 = ParagraphStyle("h2", parent=body, fontName="Helvetica-Bold", fontSize=size + 1.2,
                            leading=size + 4, spaceBefore=size * 0.75, spaceAfter=size * 0.2, textColor=INK)
        meta = ParagraphStyle("meta", parent=body, fontSize=size - 0.4, leading=(size - 0.4) * 1.35)
        story = [Paragraph(memo["subject"], h1), Spacer(1, 5)]
        rows = [[Paragraph("<b>To</b>", meta), Paragraph(memo["to"], meta)],
                [Paragraph("<b>From</b>", meta), Paragraph(memo["from"], meta)],
                [Paragraph("<b>Date</b>", meta), Paragraph(memo["date"], meta)]]
        t = Table(rows, colWidths=[0.6 * inch, 6.5 * inch])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 1), ("TOPPADDING", (0, 0), (-1, -1), 0)]))
        story += [t, Spacer(1, 6)]
        bl = Table([[Paragraph(f"<b>Bottom line.</b> {memo['bottom_line']}", body)]], colWidths=[7.26 * inch])
        bl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), HexColor("#EEF1F6")),
                                ("LINEBEFORE", (0, 0), (0, -1), 3, ULTRA),
                                ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                                ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
        story += [bl]
        for sec in memo["sections"]:
            block = [Paragraph(sec["title"], h2)]
            if "paragraph" in sec:
                block.append(Paragraph(sec["paragraph"], body))
            if sec.get("bullets"):
                items = [ListItem(Paragraph(f"<b>{lead}</b> {text}", body), leftIndent=10)
                         for lead, text in sec["bullets"]]
                block.append(ListFlowable(items, bulletType="bullet", start="\u2022", leftIndent=10,
                                          bulletFontSize=size - 2, bulletColor=ULTRA, bulletOffsetY=1,
                                          spaceBefore=0))
            story.append(KeepTogether(block))
        story += [Spacer(1, 7), Paragraph(memo["method"], small)]
        doc.build(story)
        from pypdf import PdfReader
        if len(PdfReader(str(path)).pages) == 1:
            return size
    raise RuntimeError("memo does not fit on one page")


def main():
    memo = build()
    (C.DOCS / "executive_memo.md").write_text(to_markdown(memo))
    (C.DATA_PROCESSED / "memo.json").write_text(json.dumps(memo, indent=2))
    size = to_pdf(memo, C.DOCS / "executive_memo.pdf")
    words = len(to_markdown(memo).split())
    print(f"memo written: {words} words, one page at {size:.1f}pt")


if __name__ == "__main__":
    main()
