"""
Collect every number the slide deck uses from the pipeline outputs, so the deck always
matches the app and the memo. Run after pipeline/run_all.py:
    python deck/deck_data.py && node deck/build_deck.js
"""
import json
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
import config as C  # noqa: E402
import planning as PL  # noqa: E402

P = ROOT / "data" / "processed"
load = lambda name: json.loads((P / name).read_text())
s, pl, mr, mk, ln, q = (load(n) for n in ["summary.json", "planning.json", "model_report.json", "market.json",
                                           "launch_scorecard.json", "quality_report.json"])
by = {x["name"]: x for x in pl["scenarios"]}
rec = next(x for x in pl["scenarios"] if x["name"].startswith("Recommended"))
inputs = PL.load_inputs()
plays_pts = round(pl["levers"]["bundle_pts"] + pl["levers"]["renewal_pts"], 1)
rec_params = replace(PL.Params(productivity=inputs["productivity"]), win_delta_pts=plays_pts,
                     hires_now=rec["params"]["hires_now"])
slip = PL.run(replace(rec_params, lead_months=6), inputs)

opp = pd.read_csv(C.DATA_CLEAN / "opportunities.csv", parse_dates=["created_date"])
core = opp[opp.opp_type.isin(["Land", "Expansion"])]
end = pd.Timestamp(C.AS_OF)
weekly = float(core[(core.created_date > end - pd.Timedelta(days=56)) & (core.created_date <= end)].amount.sum() / 8)

unc = next(g for g in s["coverage_gap"]["by_coverage"] if g["covered"] == 0)
cov = next(g for g in s["coverage_gap"]["by_coverage"] if g["covered"] == 1)
gaps = sorted(mr["coverage_gap"]["by_region_segment"], key=lambda r: -r["gap_pts"])[:4]
tiers = {t["tier"]: t for t in mr["icp"]["tiers"]}
growth = mk["curated"]["growth"]
facts = {f["metric"]: f for f in mk["curated"]["market"]["facts"]}
links = {k: v for k, v in C.AUTHOR_LINKS.items() if v}

data = {
    "author": C.AUTHOR,
    "github": links.get("GitHub", ""),
    "as_of_label": f"{C.AS_OF:%B} {C.AS_OF.day}, {C.AS_OF.year}",
    "fy27_target": s["fy27_target"], "fy26_bookings": s["fy26_bookings"], "growth_target": C.FY27_GROWTH_TARGET,
    "q1_pacing": s["q1_pacing"], "q1_qtd": s["q1_qtd_bookings"], "q1_plan": s["fy27_plan_by_quarter"][0],
    "q2_plan": s["fy27_plan_by_quarter"][1], "coverage": s["pipeline_coverage"],
    "weekly_pipeline": weekly,
    "unc": unc, "cov": cov, "gaps": gaps,
    "whitespace": s["whitespace"]["expected_value_total"], "half_accounts": s["whitespace"]["accounts_for_half_of_ev"],
    "non_customers": s["whitespace"]["non_customers"],
    "deal": s["deal_effects"], "levers": pl["levers"], "plays_pts": plays_pts,
    "scenarios": [{"name": x["name"], "attainment": x["attainment"], "forecast": x["forecast_total"],
                   "cost": x["new_hire_cost_fy27"], "run_rate": x["new_hire_run_rate"], "hires": x["params"]["hires_now"]}
                  for x in pl["scenarios"]],
    "baseline_forecast": by["Current plan"]["forecast_total"], "plays_forecast": by["Win-rate plays"]["forecast_total"],
    "rec_forecast": rec["forecast_total"], "rec_hires": rec["params"]["hires_now"], "rec_cost": rec["new_hire_cost_fy27"],
    "rec_run_rate": rec["new_hire_run_rate"], "hire_only": by["Hiring only"]["params"]["hires_now"],
    "hire_only_cost": by["Hiring only"]["new_hire_cost_fy27"], "slip_attainment": slip["attainment"],
    "market_growth": growth, "forecast_2029": facts.get("SASE market forecast", {}).get("value"),
    "single_vendor": facts.get("Single-vendor SASE share of market (forecast)", {}).get("value"),
    "top_six": facts.get("Top six vendors' share of SASE market", {}).get("value"),
    "tiers": tiers, "launch_lines": ln["lines"], "launch_totals": ln["totals"],
    "accounts": s["accounts"], "clean_opps": q["clean_opportunities"], "quarantined": q["quarantined_opportunities"],
    "auc": s["model"]["cv_auc_logistic"], "auc_gbm": s["model"]["cv_auc_gradient_boosting"],
    "closed_land_deals": s["deal_effects"]["closed_land_deals"],
}
(ROOT / "deck" / "deck_data.json").write_text(json.dumps(data, indent=1))
print(f"deck data written: target ${data['fy27_target']/1e6:.1f}M, plan {rec['attainment']:.1%} with "
      f"{data['rec_hires']} hires, slip-to-6-months {slip['attainment']:.1%}, weekly pipeline ${weekly/1e6:.2f}M")
print("top gaps:", [(g["region"], g["segment"], g["gap_pts"]) for g in gaps])
print("growth:", [(g["company"], g["growth"]) for g in growth])
print("tiers:", {k: (v["opps_per_100_accounts"], v["post_launch_wins"]) for k, v in tiers.items()})
