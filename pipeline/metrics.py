"""
Reference implementation of every headline metric.

The web app recomputes these live (so filters work); this module is the
source of truth used by the executive memo and by the automated check that
the app and the pipeline agree. Definitions match docs/operating_cadence/metric_dictionary.md.

Writes data/processed/summary.json
"""
from __future__ import annotations

import json
from datetime import date, timedelta

import numpy as np
import pandas as pd

import config as C

RAMP_MONTHS = 6


def months_between(a: date, b: date) -> float:
    return (b - a).days / 30.4


def ramp_factor(hire: date, on: date, ramp_months=RAMP_MONTHS) -> float:
    m = months_between(hire, on)
    return float(np.clip(m / ramp_months, 0, 1))


def load():
    acc = pd.read_csv(C.DATA_PROCESSED / "accounts_scored.csv")
    opp = pd.read_csv(C.DATA_CLEAN / "opportunities.csv",
                      parse_dates=["created_date", "close_date", "stage_entry_date", "last_push_date", "pov_start_date"])
    spec = pd.read_csv(C.DATA_CLEAN / "specialists.csv", parse_dates=["hire_date"])
    opp["fy"] = opp.close_date.dt.date.map(C.fiscal_year)
    opp["fq"] = opp.close_date.dt.date.map(C.fiscal_quarter)
    return acc, opp, spec


def main():
    acc, opp, spec = load()
    core = opp[opp.opp_type.isin(["Land", "Expansion"])]
    won = core[core.stage == "Closed Won"]
    closed = core[core.stage.isin(["Closed Won", "Closed Lost"])]
    open_ = core[core.stage.isin(C.OPEN_STAGES)]
    s = {"as_of": str(C.AS_OF), "fiscal_label": C.fq_label(C.AS_OF)}

    # Book
    s["accounts"] = int(len(acc))
    s["customers"] = int(acc.has_prisma_access.sum())
    s["attach_rate"] = round(float(acc.has_prisma_access.mean()), 4)
    s["sdwan_attach_of_customers"] = round(float(acc.loc[acc.has_prisma_access == 1, "has_prisma_sdwan"].mean()), 4)
    s["sase_arr"] = float(acc.sase_arr.sum())
    s["browser_arr"] = float(acc.browser_arr.sum())

    # Bookings
    by_fy = won.groupby("fy").amount.sum()
    s["bookings_by_fy"] = {int(k): float(v) for k, v in by_fy.items()}
    s["fy26_bookings"] = float(by_fy.get(2026, 0))
    s["fy25_bookings"] = float(by_fy.get(2025, 0))
    s["fy26_growth"] = round(s["fy26_bookings"] / s["fy25_bookings"] - 1, 4)
    q = won.groupby(["fy", "fq", "opp_type"]).amount.sum().unstack(fill_value=0).reset_index()
    s["bookings_by_quarter"] = [{"label": f"FY{int(r['fy']) % 100:02d} Q{int(r['fq'])}", "land": float(r.get("Land", 0)),
                                 "expansion": float(r.get("Expansion", 0))} for _, r in q.iterrows()]

    # Win rates (count-based, land deals)
    land_closed = closed[closed.opp_type == "Land"]
    fy26_land = land_closed[land_closed.fy == 2026]
    s["fy26_land_win_rate"] = round(float((fy26_land.stage == "Closed Won").mean()), 4)
    s["fy26_land_closed_deals"] = int(len(fy26_land))
    fy26_closed = closed[closed.fy == 2026]
    s["fy26_dollar_win_rate"] = round(float(fy26_closed.loc[fy26_closed.stage == "Closed Won", "amount"].sum()
                                            / fy26_closed.amount.sum()), 4)
    comp = land_closed.groupby("competitor").apply(lambda d: pd.Series(
        {"deals": len(d), "win_rate": (d.stage == "Closed Won").mean()}), include_groups=False)
    s["win_rate_by_competitor"] = {k: {"deals": int(v.deals), "win_rate": round(float(v.win_rate), 3)}
                                   for k, v in comp.iterrows()}
    lost = land_closed[land_closed.stage == "Closed Lost"]
    s["loss_stage_share"] = lost.loss_stage.value_counts(normalize=True).round(3).to_dict()
    s["median_cycle_days_fy26_won_land"] = float(
        (won[(won.opp_type == "Land") & (won.fy == 2026)].close_date
         - won[(won.opp_type == "Land") & (won.fy == 2026)].created_date).dt.days.median())

    # FY27 plan, pacing, and pipeline coverage
    target = s["fy26_bookings"] * (1 + C.FY27_GROWTH_TARGET)
    s["fy27_target"] = round(target, -3)
    plan_q = [target * w for w in C.QUARTER_SEASONALITY]
    s["fy27_plan_by_quarter"] = [round(p, -3) for p in plan_q]
    q1_start, q1_end = C.quarter_bounds(2027, 1)
    qtd = float(won[(won.close_date.dt.date >= q1_start) & (won.close_date.dt.date <= C.AS_OF)].amount.sum())
    elapsed = ((C.AS_OF - q1_start).days + 1) / ((q1_end - q1_start).days + 1)
    s["q1_qtd_bookings"] = qtd
    s["q1_elapsed_share"] = round(elapsed, 4)
    s["q1_attainment"] = round(qtd / plan_q[0], 4)
    s["q1_pacing"] = round(qtd / (plan_q[0] * elapsed), 4)
    cov = []
    for qn in range(1, 5):
        qs, qe = C.quarter_bounds(2027, qn)
        pipe = float(open_[(open_.close_date.dt.date >= qs) & (open_.close_date.dt.date <= qe)].amount.sum())
        remaining = plan_q[qn - 1] - (qtd if qn == 1 else 0)
        cov.append({"quarter": f"FY27 Q{qn}", "pipeline": pipe, "remaining_plan": round(remaining, -3),
                    "coverage": round(pipe / remaining, 2) if remaining > 0 else None})
    s["pipeline_coverage"] = cov
    s["open_pipeline_total"] = float(open_.amount.sum())
    tv = open_[open_.stage == "Technical Validation"]
    days_in = (pd.Timestamp(C.AS_OF) - tv.stage_entry_date).dt.days
    s["tv_open_deals"] = int(len(tv))
    s["tv_stalled_deals"] = int((days_in > C.STAGE_SLA_DAYS["Technical Validation"]).sum())
    s["tv_stalled_amount"] = float(tv.loc[days_in > C.STAGE_SLA_DAYS["Technical Validation"], "amount"].sum())

    # Planning-model inputs
    fy26_start, fy26_end = date(2025, 8, 1), date(2026, 7, 31)
    covered_bookings = float(won[(won.fy == 2026) & (won.specialist_covered == 1)].amount.sum())
    uncovered_bookings = float(won[(won.fy == 2026) & (won.specialist_covered == 0)].amount.sum())
    month_starts = [date(2025 + (7 + k) // 12, (7 + k) % 12 + 1, 15) for k in range(12)]
    ramped_fte = np.mean([sum(ramp_factor(h.date(), d) for h in spec.hire_date) for d in month_starts])
    s["planning"] = {
        "specialists": int(len(spec)),
        "specialists_ramping_now": int(sum(ramp_factor(h.date(), C.AS_OF) < 1 for h in spec.hire_date)),
        "fy26_covered_bookings": covered_bookings,
        "fy26_uncovered_bookings": uncovered_bookings,
        "fy26_avg_ramped_fte": round(float(ramped_fte), 2),
        "productivity_per_ramped_specialist": round(covered_bookings / ramped_fte, -3),
        "core_baseline_growth": 0.10,
        "ramp_months": RAMP_MONTHS,
        "attrition": 0.15,
        "hiring_lead_months": 3,
        "specialist_cost": C.SPECIALIST_COST,
    }

    report = json.loads((C.DATA_PROCESSED / "model_report.json").read_text())
    s["model"] = {k: report["model"][k] for k in ["cv_auc_logistic", "cv_auc_gradient_boosting",
                                                  "top_decile_lift", "top3_decile_capture"]}
    s["whitespace"] = report["whitespace"]
    s["coverage_gap"] = {"by_coverage": report["coverage_gap"]["by_coverage"],
                         "uncovered_share_of_ev": report["coverage_gap"]["uncovered_share_of_ev"]}
    s["deal_effects"] = report["deal_effects"]
    s["icp_tiers"] = report["icp"]["tiers"]

    (C.DATA_PROCESSED / "summary.json").write_text(json.dumps(s, indent=2, default=str))
    print(json.dumps({k: s[k] for k in ["attach_rate", "sase_arr", "fy25_bookings", "fy26_bookings", "fy26_growth",
                                        "fy26_land_win_rate", "fy26_dollar_win_rate", "fy27_target", "q1_qtd_bookings",
                                        "q1_attainment", "q1_pacing", "pipeline_coverage", "tv_open_deals",
                                        "tv_stalled_deals", "median_cycle_days_fy26_won_land", "planning"]},
                     indent=1, default=str))


if __name__ == "__main__":
    main()
