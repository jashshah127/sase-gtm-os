"""
FY27 capacity planning engine (Python reference implementation).

The interactive simulator in the web app runs the same math in JavaScript;
tests/check_app.py asserts both return the same attainment for the same inputs.

Model, monthly from Aug 2026 (m=0) to Jul 2027 (m=11):
  * Aug and Sep are actuals (bookings through the as-of date).
  * Forecast months Oct..Jul:
      capacity(m) = productivity x w(m) x productive_FTE(m) x win_mult x deal_mult
                    + core_baseline x w(m) x win_mult x deal_mult
    where w(m) is the month's share of annual bookings (quarter seasonality / 3).
  * productive_FTE = existing specialists x survival x ramp
                     + backfills for attrition (hired `lead` months after a departure, then ramping)
                     + new hires (approved now or in Q2, start after `lead` months, then ramping)
  * ramp(t) = clip((t + 0.5) / ramp_months, 0, 1), t = months since start (mid-month convention)
  * win_mult = (win_rate + delta_pts) / win_rate ;  deal_mult = 1 + deal_size_change
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, replace
from datetime import date

import pandas as pd

import config as C

AUG1 = date(2026, 8, 1)


@dataclass
class Params:
    growth: float = C.FY27_GROWTH_TARGET
    productivity: float = 2_000_000
    ramp_months: int = 6
    attrition: float = 0.15
    lead_months: int = 3
    hires_now: int = 0
    hires_q2: int = 0
    win_delta_pts: float = 0.0
    deal_delta: float = 0.0
    partner_lift: float = 0.0


def ramp(t: float, r: int) -> float:
    if t < 0:
        return 0.0
    return min(1.0, (t + 0.5) / r)


def weights():
    return [C.QUARTER_SEASONALITY[m // 3] / 3 for m in range(12)]


def run(p: Params, inputs: dict) -> dict:
    w = weights()
    target = inputs["fy26_bookings"] * (1 + p.growth)
    win_mult = (inputs["win_rate"] + p.win_delta_pts / 100) / inputs["win_rate"]
    deal_mult = 1 + p.deal_delta
    s = (1 - p.attrition) ** (1 / 12)
    surv = [s ** max(0, m - 1) for m in range(12)]
    starts = inputs["specialist_start_months"]          # months from Aug 1, 2026 (negative = hired earlier)
    n_exist = len(starts)
    core = inputs["core_baseline"] * (1 + p.partner_lift)

    new_cohorts = []
    if p.hires_now:
        new_cohorts.append((2 + p.lead_months, p.hires_now))
    if p.hires_q2:
        new_cohorts.append((3 + p.lead_months, p.hires_q2))

    months = []
    for m in range(12):
        exist = sum(ramp(m - st, p.ramp_months) for st in starts) * surv[m]
        backfill = n_exist * sum((surv[k - 1] - surv[k]) * ramp(m - (k + p.lead_months), p.ramp_months)
                                 for k in range(2, 12))
        new = sum(n * (s ** max(0, m - st)) * ramp(m - st, p.ramp_months) for st, n in new_cohorts)
        spec_cap = p.productivity * w[m] * (exist + backfill) * win_mult * deal_mult
        new_cap = p.productivity * w[m] * new * win_mult * deal_mult
        core_cap = core * w[m] * win_mult * deal_mult
        months.append({"m": m, "fte_existing": exist + backfill, "fte_new": new,
                       "capacity": spec_cap + new_cap + core_cap, "capacity_new": new_cap})

    actual = inputs["actual_by_month"]                  # Aug, Sep (to date)
    forecast = sum(mo["capacity"] for mo in months[2:])
    total = actual[0] + actual[1] + forecast
    new_arr = sum(mo["capacity_new"] for mo in months[2:])
    new_cost = sum(n * max(0, 12 - st) * inputs["specialist_cost"] / 12 for st, n in new_cohorts)
    run_rate_new = sum(n for _, n in new_cohorts) * p.productivity * win_mult * deal_mult
    return {"target": target, "forecast_total": total, "attainment": total / target, "gap": target - total,
            "new_hire_arr_fy27": new_arr, "new_hire_cost_fy27": new_cost, "new_hire_run_rate": run_rate_new,
            "months": months}


def hires_needed(p: Params, inputs: dict, cap: int = 60):
    for h in range(cap + 1):
        if run(replace(p, hires_now=h), inputs)["attainment"] >= 1.0:
            return h
    return None


def load_inputs() -> dict:
    summary = json.loads((C.DATA_PROCESSED / "summary.json").read_text())
    spec = pd.read_csv(C.DATA_CLEAN / "specialists.csv", parse_dates=["hire_date"])
    opp = pd.read_csv(C.DATA_CLEAN / "opportunities.csv", parse_dates=["close_date"])
    won = opp[(opp.stage == "Closed Won") & opp.opp_type.isin(["Land", "Expansion"])]
    aug = won[(won.close_date >= "2026-08-01") & (won.close_date <= "2026-08-31")].amount.sum()
    sep = won[(won.close_date >= "2026-09-01") & (won.close_date <= str(C.AS_OF))].amount.sum()
    pl = summary["planning"]
    return {
        "fy26_bookings": summary["fy26_bookings"],
        "win_rate": summary["fy26_land_win_rate"],
        "core_baseline": pl["fy26_uncovered_bookings"] * (1 + pl["core_baseline_growth"]),
        "specialist_start_months": [(h.date() - AUG1).days / 30.4 for h in spec.hire_date],
        "actual_by_month": [float(aug), float(sep)],
        "specialist_cost": pl["specialist_cost"],
        "productivity": pl["productivity_per_ramped_specialist"],
    }


def win_rate_levers(summary: dict, opp: pd.DataFrame) -> dict:
    """Translate deal-level effects into blended win-rate points for the simulator."""
    land = opp[(opp.opp_type == "Land") & opp.stage.isin(["Closed Won", "Closed Lost"])]
    sse = land.competitor.isin(["Zscaler", "Netskope"])
    de = summary["deal_effects"]
    share_sse = float(sse.mean())
    bundle_now = float(land.loc[sse, "sdwan_bundle"].mean())
    aligned_now = float(land.renewal_aligned.mean())
    bundle_target, aligned_target = 0.75, 0.50
    bundle_pts = share_sse * max(0, bundle_target - bundle_now) * (de["adj_win_sse_bundle"] - de["adj_win_sse_no_bundle"]) * 100
    renewal_pts = max(0, aligned_target - aligned_now) * (de["adj_win_aligned"] - de["adj_win_not_aligned"]) * 100
    return {"share_sse_deals": round(share_sse, 3), "bundle_share_in_sse_now": round(bundle_now, 3),
            "bundle_share_target": bundle_target, "bundle_pts": round(bundle_pts, 1),
            "aligned_share_now": round(aligned_now, 3), "aligned_share_target": aligned_target,
            "renewal_pts": round(renewal_pts, 1)}


def scenarios(inputs: dict, levers: dict) -> list:
    base = Params(productivity=inputs["productivity"])
    plays = round(levers["bundle_pts"] + levers["renewal_pts"], 1)
    with_plays = replace(base, win_delta_pts=plays)
    rec_hires = hires_needed(with_plays, inputs)
    defs = [
        ("Current plan", "Today's specialists, backfills for attrition, no new hires", base),
        ("Hire 6 specialists now", "Approved this month, productive after lead time and ramp", replace(base, hires_now=6)),
        ("Win-rate plays", f"SD-WAN bundle in rival deals (+{levers['bundle_pts']} pts) and renewal timing (+{levers['renewal_pts']} pts)", with_plays),
        (f"Recommended: plays + {rec_hires} hires", "Smallest hiring plan that reaches 100% with both plays in place", replace(with_plays, hires_now=rec_hires or 0)),
        ("Hiring only", "Hires needed now if nothing else changes", replace(base, hires_now=hires_needed(base, inputs) or 0)),
    ]
    base_total = run(base, inputs)["forecast_total"]
    out = []
    for name, desc, p in defs:
        r = run(p, inputs)
        out.append({"name": name, "description": desc, "params": asdict(p),
                    "attainment": round(r["attainment"], 4), "forecast_total": round(r["forecast_total"], -3),
                    "incremental_vs_current": round(r["forecast_total"] - base_total, -3),
                    "new_hire_cost_fy27": round(r["new_hire_cost_fy27"], -3),
                    "new_hire_run_rate": round(r["new_hire_run_rate"], -3)})
    return out


def main():
    inputs = load_inputs()
    summary = json.loads((C.DATA_PROCESSED / "summary.json").read_text())
    opp = pd.read_csv(C.DATA_CLEAN / "opportunities.csv")
    levers = win_rate_levers(summary, opp)
    sc = scenarios(inputs, levers)
    base = run(Params(productivity=inputs["productivity"]), inputs)
    result = {"inputs": inputs, "levers": levers, "scenarios": sc,
              "baseline": {k: base[k] for k in ["target", "forecast_total", "attainment", "gap"]},
              "hires_needed_alone": hires_needed(Params(productivity=inputs["productivity"]), inputs)}
    (C.DATA_PROCESSED / "planning.json").write_text(json.dumps(result, indent=2))
    print(f"target=${base['target']/1e6:.2f}M forecast=${base['forecast_total']/1e6:.2f}M "
          f"attainment={base['attainment']:.1%} hires needed alone={result['hires_needed_alone']}")
    print("levers:", levers)
    for s in sc:
        print(f"  {s['name']:<34} attain={s['attainment']:.1%}  +${s['incremental_vs_current']/1e6:.2f}M  "
              f"cost=${s['new_hire_cost_fy27']/1e6:.2f}M  run-rate=${s['new_hire_run_rate']/1e6:.1f}M")


if __name__ == "__main__":
    main()
