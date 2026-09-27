"""
Prisma Browser launch scorecard, weekly since the March 23, 2026 relaunch.

Actuals come from post-relaunch Browser opportunities. The launch plan is
synthetic: a ramp-to-steady-state curve per metric, sized so the scorecard
has a realistic mix of on-track and at-risk lines.

Writes data/processed/launch_scorecard.json
"""
from __future__ import annotations

import json
from datetime import timedelta

import numpy as np
import pandas as pd

import config as C

# Plan sizing: actual cumulative / plan cumulative at the as-of week
PLAN_ATTAINMENT = {"pipeline": 0.94, "povs": 0.78, "wins": 0.88}
PLAN_SHAPE = {"pipeline": (0, 8), "povs": (2, 8), "wins": (6, 8)}   # (weeks of zero, weeks to steady state)
ENABLEMENT_TARGET, ENABLEMENT_TARGET_WEEK = 0.80, 12


def status(ratio: float, good=0.95, watch=0.85) -> str:
    return "On track" if ratio >= good else ("Watch" if ratio >= watch else "At risk")


def main():
    opp = pd.read_csv(C.DATA_CLEAN / "opportunities.csv", parse_dates=["created_date", "close_date", "pov_start_date"])
    en = pd.read_csv(C.DATA_CLEAN / "launch_enablement_weekly.csv", parse_dates=["week_start"])
    start = pd.Timestamp(C.BROWSER_RELAUNCH)
    asof = pd.Timestamp(C.AS_OF)
    n_weeks = (asof - start).days // 7 + 1
    weeks = [start + timedelta(days=7 * k) for k in range(n_weeks)]
    post = opp[(opp.opp_type == "Browser") & (opp.created_date >= start)]

    def weekly(dates, values=None):
        idx = ((dates - start).dt.days // 7)
        s = (values if values is not None else pd.Series(1, index=dates.index)).groupby(idx).sum()
        return [float(s.get(k, 0)) for k in range(n_weeks)]

    actual = {
        "pipeline": weekly(post.created_date, post.amount),
        "povs": weekly(post.pov_start_date.dropna()),
        "wins": weekly(post.loc[post.stage == "Closed Won", "close_date"]),
        "win_arr": weekly(post.loc[post.stage == "Closed Won", "close_date"], post.loc[post.stage == "Closed Won", "amount"]),
    }
    plans, lines = {}, []
    for key, att in PLAN_ATTAINMENT.items():
        zero, ramp = PLAN_SHAPE[key]
        shape = np.array([0 if k < zero else min(1.0, (k - zero + 1) / ramp) for k in range(n_weeks)])
        total_actual = sum(actual[key])
        scale = (total_actual / att) / shape.sum()
        plans[key] = (shape * scale).round(0 if key != "pipeline" else -2).tolist()
        cum_a, cum_p = float(np.sum(actual[key])), float(np.sum(plans[key]))
        lines.append({"metric": {"pipeline": "Pipeline created", "povs": "POVs started", "wins": "Deals won"}[key],
                      "actual": cum_a, "plan": cum_p, "attainment": round(cum_a / cum_p, 3),
                      "status": status(cum_a / cum_p)})

    enable = {}
    for r in C.REGIONS:
        s = en[en.region == r].sort_values("week_start")
        enable[r] = s.certified_pct.round(3).tolist()[:n_weeks]
        cur = enable[r][-1]
        lines.append({"metric": f"Field certified, {r}", "actual": cur, "plan": ENABLEMENT_TARGET,
                      "attainment": round(cur / ENABLEMENT_TARGET, 3),
                      "status": "On track" if cur >= ENABLEMENT_TARGET else ("Watch" if cur >= 0.70 else "At risk")})
    enable_plan = [round(min(ENABLEMENT_TARGET, ENABLEMENT_TARGET * (k + 1) / ENABLEMENT_TARGET_WEEK), 3)
                   for k in range(n_weeks)]
    heads = en.groupby("region").field_headcount.first().to_dict()

    closed = post[post.stage.isin(["Closed Won", "Closed Lost"])]
    pov_reached = post.pov_start_date.notna()
    out = {
        "weeks": [w.strftime("%Y-%m-%d") for w in weeks],
        "actual": actual, "plan": plans, "enablement": enable, "enablement_plan": enable_plan,
        "field_headcount": heads, "lines": lines,
        "totals": {
            "opps": int(len(post)), "open": int(post.stage.isin(C.OPEN_STAGES).sum()),
            "wins": int((post.stage == "Closed Won").sum()),
            "win_rate": round(float((closed.stage == "Closed Won").mean()), 3),
            "win_arr": float(post.loc[post.stage == "Closed Won", "amount"].sum()),
            "pipeline": float(post.amount.sum()),
            "pov_to_win": round(float((post.stage == "Closed Won").sum() / max(pov_reached.sum(), 1)), 3),
            "lost_at_pov_share": round(float((closed.loss_stage == "Technical Validation").sum()
                                             / max((closed.stage == "Closed Lost").sum(), 1)), 3),
        },
    }
    (C.DATA_PROCESSED / "launch_scorecard.json").write_text(json.dumps(out, indent=2))
    for ln in lines:
        print(f"  {ln['metric']:<24} actual={ln['actual']:>12,.2f} plan={ln['plan']:>12,.2f} {ln['attainment']:.0%} {ln['status']}")
    print("totals:", out["totals"])


if __name__ == "__main__":
    main()
