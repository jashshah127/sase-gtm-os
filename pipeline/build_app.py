"""
Assemble the web app into ONE self-contained file: index.html at the repo root.

Data (compact, columnar JSON), styles, and scripts are inlined so the app works
offline, loads instantly, and deploys to GitHub Pages with no build server.

Reads  data/clean, data/processed, docs/, app/
Writes index.html
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import markdown
import pandas as pd

import config as C
from content import FUNCTIONS, METRICS, ONBOARDING, PLANNING_CALENDAR, RACI, RHYTHM
from write_docs import SOURCES

# Overrides exist only so tests can render the app against fixture data without touching the real build.
MARKET_JSON = Path(os.environ.get("MARKET_JSON", C.DATA_PROCESSED / "market.json"))
OUTPUT_HTML = Path(os.environ.get("OUTPUT_HTML", C.ROOT / "index.html"))
JS_FILES = ["core.js", "charts.js", "views_a.js", "planning.js", "views_b.js", "view_market.js", "main.js"]


def days(series):
    d = pd.to_datetime(pd.Series(series), errors="coerce")
    delta = (d - pd.Timestamp(C.EPOCH)).dt.days
    return [None if pd.isna(v) else int(v) for v in delta]


def codes(series, lookup, required=True):
    m = {v: i for i, v in enumerate(lookup)}
    out = [m.get(v) if isinstance(v, str) else None for v in series]
    if required:
        missing = sorted({v for v, o in zip(series, out) if o is None})
        assert not missing, f"values missing from lookup: {missing[:5]}"
    return out


def ints(series):
    return pd.Series(series).round().astype(int).tolist()


def md(text: str) -> str:
    return markdown.markdown(text, extensions=["tables"])


def build_payload() -> dict:
    acc = pd.read_csv(C.DATA_PROCESSED / "accounts_scored.csv")
    opp = pd.read_csv(C.DATA_CLEAN / "opportunities.csv")
    terr = pd.read_csv(C.DATA_CLEAN / "territories.csv")
    spec = pd.read_csv(C.DATA_CLEAN / "specialists.csv")
    load = lambda name: json.loads((C.DATA_PROCESSED / name).read_text())
    summary, model, planning = load("summary.json"), load("model_report.json"), load("planning.json")
    launch, quality, memo = load("launch_scorecard.json"), load("quality_report.json"), load("memo.json")

    tids = terr.territory_id.tolist()
    acc_index = {a: i for i, a in enumerate(acc.account_id)}
    renew = (pd.to_datetime(acc.ngfw_renewal_date) - pd.Timestamp(C.AS_OF)).dt.days

    A = {
        "id": acc.account_id.tolist(), "nm": acc.account_name.tolist(),
        "sg": codes(acc.segment, C.SEGMENTS), "rg": codes(acc.region, C.REGIONS),
        "in": codes(acc.industry, C.INDUSTRIES), "tr": codes(acc.territory_id, tids),
        "em": ints(acc.employees), "br": ints(acc.branch_count),
        "rm": ints(acc.remote_workforce_pct * 100), "cn": ints(acc.contractor_pct * 100),
        "um": ints(acc.unmanaged_device_pct * 100), "vd": ints(acc.vdi_in_use),
        "ic": codes(acc.incumbent_remote_access, C.INCUMBENTS),
        "pa": ints(acc.has_prisma_access), "sw": ints(acc.has_prisma_sdwan),
        "bw": ints(acc.has_prisma_browser), "be": ints(acc.browser_early_adopter),
        "ar": ints(acc.sase_arr), "ba": ints(acc.browser_arr), "ng": ints(acc.ngfw_arr),
        "lp": ints(acc.land_potential_arr), "fp": ints(acc.full_potential_arr),
        "pr": ints(acc.propensity * 10000),
        "pl": [C.PLAYS.index(p) if isinstance(p, str) and p in C.PLAYS else -1 for p in acc.play],
        "rn": ints(renew), "is": ints(acc.icp_score), "fd": days(acc.sase_first_purchase_date),
    }
    O = {
        "id": [int(x[1:]) for x in opp.opp_id], "a": [acc_index[a] for a in opp.account_id],
        "t": codes(opp.opp_type, C.OPP_TYPES), "p": codes(opp["product"], C.PRODUCTS),
        "c": days(opp.created_date), "l": days(opp.close_date), "s": codes(opp.stage, C.STAGES),
        "m": ints(opp.amount), "k": codes(opp.competitor, C.COMPETITORS), "b": ints(opp.sdwan_bundle),
        "o": codes(opp.source, C.SOURCES), "r": codes(opp.loss_reason, C.LOSS_REASONS, required=False),
        "x": codes(opp.loss_stage, C.STAGES, required=False), "e": days(opp.stage_entry_date),
        "u": ints(opp.push_count), "q": days(opp.last_push_date), "n": ints(opp.renewal_aligned),
        "v": days(opp.pov_start_date),
    }
    T = {"id": tids, "rg": codes(terr.region, C.REGIONS), "sg": codes(terr.segment, C.SEGMENTS),
         "cv": ints(terr.specialist_covered), "sp": terr.specialist_id.fillna("").tolist()}
    SP = {"id": spec.specialist_id.tolist(), "nm": spec.specialist_name.tolist(),
          "rg": codes(spec.region, C.REGIONS), "sg": codes(spec.segment, C.SEGMENTS), "h": days(spec.hire_date)}

    q1_start, _ = C.quarter_bounds(2027, 1)
    kit = C.DOCS / "launch_kit"
    m = model["model"]
    return {
        "meta": {
            "asOf": days([C.AS_OF])[0], "asOfLabel": f"{C.AS_OF:%b} {C.AS_OF.day}, {C.AS_OF.year}",
            "fiscalLabel": C.fq_label(C.AS_OF), "weekOfQuarter": (C.AS_OF - q1_start).days // 7 + 1,
            "relaunch": days([C.BROWSER_RELAUNCH])[0], "author": C.AUTHOR,
            "links": {k: v for k, v in C.AUTHOR_LINKS.items() if v},
        },
        "lk": {"segments": C.SEGMENTS, "regions": C.REGIONS, "industries": C.INDUSTRIES,
               "incumbents": C.INCUMBENTS, "competitors": C.COMPETITORS, "stages": C.STAGES,
               "sources": C.SOURCES, "lossReasons": C.LOSS_REASONS, "products": C.PRODUCTS,
               "types": C.OPP_TYPES, "plays": C.PLAYS},
        "cfg": {"growth": C.FY27_GROWTH_TARGET, "seasonality": C.QUARTER_SEASONALITY,
                "stageSla": [C.STAGE_SLA_DAYS[s] for s in C.OPEN_STAGES],
                "specialistCost": C.SPECIALIST_COST, "rampMonths": summary["planning"]["ramp_months"],
                "attrition": summary["planning"]["attrition"], "lead": summary["planning"]["hiring_lead_months"],
                "accountsPerSpecialist": [C.ACCOUNTS_PER_SPECIALIST[s] for s in C.SEGMENTS],
                "browserPrice": C.BROWSER_PRICE_PER_USER, "dollarWinRate": summary["fy26_dollar_win_rate"]},
        "acc": A, "opp": O, "terr": T, "spec": SP,
        "summary": summary,
        "model": {"lift": m["lift"], "drivers": m["drivers"], "auc": m["cv_auc_logistic"],
                  "gbm": m["cv_auc_gradient_boosting"], "trainRate": m["train_adopters"] / m["train_accounts"],
                  "topDecileLift": m["top_decile_lift"], "top3": m["top3_decile_capture"]},
        "icp": {"table": model["icp"]["table"], "cutoffs": model["icp"]["tier_cutoffs"],
                "tiers": model["icp"]["tiers"], "early_adopters": model["icp"]["early_adopters"]},
        "planning": planning, "launch": launch, "quality": quality, "memo": memo,
        "content": {"metrics": METRICS, "functions": FUNCTIONS, "raci": [list(r) for r in RACI],
                    "rhythm": [{"cadence": b["cadence"], "items": [list(i) for i in b["items"]]} for b in RHYTHM],
                    "calendar": [list(c) for c in PLANNING_CALENDAR]},
        "docs": {"icp": md((kit / "01_icp.md").read_text()), "positioning": md((kit / "02_positioning.md").read_text()),
                 "battlecard": md((kit / "03_battlecard.md").read_text()),
                 "discovery": md((kit / "04_discovery_guide.md").read_text()),
                 "scorecard": md((kit / "05_launch_scorecard.md").read_text()), "onboarding": md(ONBOARDING)},
        "sources": [{"fact": f, "source": s, "url": u} for f, s, u in SOURCES],
        "market": json.loads(MARKET_JSON.read_text()) if MARKET_JSON.exists() else None,
    }


def main():
    payload = build_payload()
    data = json.dumps(payload, separators=(",", ":"), allow_nan=False).replace("</", "<\\/")
    tpl = (C.APP / "index.template.html").read_text()
    css = (C.APP / "styles.css").read_text()
    js = "\n".join((C.APP / f).read_text() for f in JS_FILES)
    for marker in ("/*__CSS__*/", "/*__JS__*/", "__DATA__"):
        assert tpl.count(marker) == 1, f"template must contain {marker} exactly once"
    assert "__DATA__" not in css + js and "</script" not in js.lower()
    html = tpl.replace("/*__CSS__*/", css).replace("/*__JS__*/", js).replace("__DATA__", data)
    OUTPUT_HTML.write_text(html)
    print(f"{OUTPUT_HTML.name} written: {len(html) / 1024:.0f} KB (data {len(data) / 1024:.0f} KB, "
          f"{len(payload['acc']['id'])} accounts, {len(payload['opp']['id'])} opportunities)")


if __name__ == "__main__":
    main()
