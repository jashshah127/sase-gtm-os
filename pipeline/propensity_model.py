"""
Revenue-opportunity analytics:

1. SASE attach propensity (look-alike model)
   Trained ONLY on accounts in specialist-covered territories, where the SASE
   motion has been fully expressed. The score therefore answers: "how likely is
   this account to be a Prisma Access customer under good coverage?" Region and
   coverage are excluded on purpose; they describe our go-to-market, not the
   customer's need.

2. Whitespace sizing and prioritization (propensity x land potential)
3. Coverage gap: actual attach vs. modeled attach, by territory
4. Deal-level adjusted effects (does the SD-WAN bundle really help vs. SSE rivals?)
5. Prisma Browser ICP: lift-based points scorecard, validated out-of-time on
   post-relaunch deals

Reads data/clean/*.csv. Writes data/processed/accounts_scored.csv and model_report.json.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import config as C

NUMERIC = ["remote_workforce_pct", "log_branches", "log_employees", "contractor_pct",
           "unmanaged_device_pct", "vdi_in_use", "cortex_xdr", "cortex_cloud", "health_score", "tenure_years"]
CATEGORICAL = ["segment", "industry", "incumbent_remote_access"]
REFERENCE = {"segment": "Mid-Market", "industry": "Manufacturing", "incumbent_remote_access": "Third-party VPN"}
LABELS = {
    "remote_workforce_pct": "Remote workforce share", "log_branches": "Branch footprint",
    "log_employees": "Employee count", "contractor_pct": "Contractor share",
    "unmanaged_device_pct": "Unmanaged device share", "vdi_in_use": "Runs VDI",
    "cortex_xdr": "Owns Cortex XDR", "cortex_cloud": "Owns Cortex Cloud",
    "health_score": "Customer health score", "tenure_years": "Years as a customer",
}


def features(acc: pd.DataFrame) -> pd.DataFrame:
    X = acc[CATEGORICAL + ["remote_workforce_pct", "contractor_pct", "unmanaged_device_pct", "vdi_in_use",
                           "cortex_xdr", "cortex_cloud", "health_score"]].copy()
    X["log_branches"] = np.log1p(acc.branch_count)
    X["log_employees"] = np.log(acc.employees)
    X["tenure_years"] = C.AS_OF.year - acc.customer_since
    return X


def build_model(kind="logit"):
    cats = [sorted(set([REFERENCE[c]])) for c in CATEGORICAL]
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(drop=[REFERENCE[c] for c in CATEGORICAL], handle_unknown="ignore"), CATEGORICAL),
    ])
    if kind == "logit":
        est = LogisticRegression(C=1.0, max_iter=5000)
    else:
        est = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300, random_state=C.SEED)
    return Pipeline([("pre", pre), ("est", est)])


def assign_play(row) -> str:
    if row.incumbent_remote_access in C.SSE_COMPETITORS:
        return "Competitive displacement"
    days = (pd.Timestamp(row.ngfw_renewal_date) - pd.Timestamp(C.AS_OF)).days
    if 90 <= days <= 270:
        return "Renewal-timed attach"
    if row.incumbent_remote_access == "GlobalProtect VPN":
        return "GlobalProtect migration"
    if row.branch_q75:
        return "Branch transformation"
    return "Partner-led nurture"


def main():
    acc = pd.read_csv(C.DATA_CLEAN / "accounts.csv")
    opp = pd.read_csv(C.DATA_CLEAN / "opportunities.csv", parse_dates=["created_date", "close_date"])
    X = features(acc)
    y = acc.has_prisma_access.to_numpy()
    covered = acc.specialist_covered.to_numpy() == 1
    report = {}

    # ---------------- 1. Propensity model ----------------
    Xc, yc = X[covered], y[covered]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=C.SEED)
    cv_logit = cross_val_predict(build_model("logit"), Xc, yc, cv=cv, method="predict_proba")[:, 1]
    cv_gbm = cross_val_predict(build_model("gbm"), Xc, yc, cv=cv, method="predict_proba")[:, 1]
    auc_logit, auc_gbm = roc_auc_score(yc, cv_logit), roc_auc_score(yc, cv_gbm)

    model = build_model("logit").fit(Xc, yc)
    acc["propensity"] = model.predict_proba(X)[:, 1].round(4)

    # Lift table on out-of-fold predictions
    order = np.argsort(-cv_logit)
    deciles = np.empty(len(order), dtype=int)
    deciles[order] = np.arange(len(order)) * 10 // len(order) + 1
    lift = []
    total_pos = yc.sum()
    for d in range(1, 11):
        m = deciles == d
        lift.append({"decile": d, "accounts": int(m.sum()), "adopters": int(yc[m].sum()),
                     "attach_rate": round(float(yc[m].mean()), 3),
                     "cum_capture": round(float(yc[deciles <= d].sum() / total_pos), 3)})

    # Drivers from standardized coefficients
    names = model.named_steps["pre"].get_feature_names_out()
    coefs = model.named_steps["est"].coef_[0]
    drivers = []
    for n, c in zip(names, coefs):
        kind, feat = n.split("__", 1)
        if kind == "num":
            label = f"{LABELS[feat]} (+1 SD)"
        else:
            col = next(cc for cc in CATEGORICAL if feat.startswith(cc + "_"))
            val = feat[len(col) + 1:]
            ref = REFERENCE[col]
            pretty = {"segment": "Segment", "industry": "Industry", "incumbent_remote_access": "Incumbent"}[col]
            label = f"{pretty}: {val} (vs {ref})"
        drivers.append({"driver": label, "coef": round(float(c), 3), "odds_ratio": round(float(math.exp(c)), 2)})
    drivers.sort(key=lambda d: -abs(d["coef"]))
    report["model"] = {
        "method": "Logistic regression (standardized numerics, one-hot categoricals), trained on specialist-covered accounts only",
        "train_accounts": int(covered.sum()), "train_adopters": int(yc.sum()),
        "cv_auc_logistic": round(auc_logit, 3), "cv_auc_gradient_boosting": round(auc_gbm, 3),
        "lift": lift, "drivers": drivers[:12],
        "top_decile_lift": round(lift[0]["attach_rate"] / float(yc.mean()), 2),
        "top3_decile_capture": lift[2]["cum_capture"],
    }

    # ---------------- 2. Whitespace ----------------
    non = acc.has_prisma_access == 0
    acc["expected_value"] = np.where(non, (acc.propensity * acc.land_potential_arr).round(-2), 0)
    acc["expansion_whitespace"] = np.where(~non, (acc.full_potential_arr - acc.sase_arr).clip(lower=0).round(-2), 0)
    q75 = acc.groupby("segment").branch_count.transform(lambda s: s.quantile(0.75))
    acc["branch_q75"] = acc.branch_count >= q75
    acc["play"] = acc.apply(assign_play, axis=1)
    acc.loc[~non, "play"] = ""
    acc = acc.drop(columns="branch_q75")
    ev = acc.loc[non].sort_values("expected_value", ascending=False)
    cum = ev.expected_value.cumsum() / ev.expected_value.sum()
    n_top = int((cum <= 0.5).sum()) + 1
    report["whitespace"] = {
        "non_customers": int(non.sum()),
        "land_potential_total": float(acc.loc[non, "land_potential_arr"].sum()),
        "expected_value_total": float(acc.loc[non, "expected_value"].sum()),
        "accounts_for_half_of_ev": n_top,
        "share_of_accounts_for_half": round(n_top / int(non.sum()), 3),
        "expansion_whitespace_total": float(acc.expansion_whitespace.sum()),
        "ev_by_play": acc.loc[non].groupby("play").expected_value.sum().round(-3).to_dict(),
    }

    # ---------------- 3. Coverage gap ----------------
    g = acc.groupby("territory_id").agg(region=("region", "first"), segment=("segment", "first"),
                                          covered=("specialist_covered", "first"), accounts=("account_id", "size"),
                                          actual=("has_prisma_access", "mean"), modeled=("propensity", "mean"),
                                          adopters=("has_prisma_access", "sum"), expected_adopters=("propensity", "sum"))
    gap = []
    for (cov_flag), grp in acc.groupby("specialist_covered"):
        gap.append({"covered": int(cov_flag), "accounts": int(len(grp)),
                    "actual_attach": round(float(grp.has_prisma_access.mean()), 3),
                    "modeled_attach": round(float(grp.propensity.mean()), 3),
                    "latent_customers": int(round(grp.propensity.sum() - grp.has_prisma_access.sum()))})
    rs = acc.groupby(["region", "segment"]).agg(accounts=("account_id", "size"),
                                                  covered_share=("specialist_covered", "mean"),
                                                  actual=("has_prisma_access", "mean"),
                                                  modeled=("propensity", "mean")).reset_index()
    rs["gap_pts"] = ((rs.modeled - rs.actual) * 100).round(1)
    unc = acc[acc.specialist_covered == 0]
    latent_ev = float((unc.propensity - unc.has_prisma_access).clip(lower=0).mul(unc.land_potential_arr).sum())
    report["coverage_gap"] = {
        "by_coverage": gap,
        "by_region_segment": rs.round(3).to_dict(orient="records"),
        "uncovered_latent_ev": round(latent_ev, -3),
        "uncovered_share_of_ev": round(float(acc.loc[non & (acc.specialist_covered == 0), "expected_value"].sum()
                                             / acc.loc[non, "expected_value"].sum()), 3),
    }

    # ---------------- 4. Adjusted deal-level effects ----------------
    land = opp[(opp.opp_type == "Land") & opp.stage.isin(["Closed Won", "Closed Lost"])].copy()
    land = land.merge(acc[["account_id", "segment"]], on="account_id", how="left")
    land["won"] = (land.stage == "Closed Won").astype(int)
    land["sse_rival"] = land.competitor.isin(["Zscaler", "Netskope"]).astype(int)
    land["partner"] = (land.source == "Partner-sourced").astype(int)
    D = pd.get_dummies(land[["segment"]], drop_first=True).astype(float)
    D["bundle"] = land.sdwan_bundle
    D["sse_rival"] = land.sse_rival
    D["bundle_x_sse"] = land.sdwan_bundle * land.sse_rival
    D["no_comp"] = (land.competitor == "No competitor").astype(int)
    D["covered"] = land.specialist_covered
    D["aligned"] = land.renewal_aligned
    D["partner"] = land.partner
    lr = LogisticRegression(C=10.0, max_iter=5000).fit(D, land.won)

    def cf(mask, **sets):
        Z = D[mask].copy()
        for k, v in sets.items():
            Z[k] = v
        if "bundle" in sets:
            Z["bundle_x_sse"] = Z["bundle"] * Z["sse_rival"]
        return float(lr.predict_proba(Z)[:, 1].mean())

    sse = land.sse_rival == 1
    raw_b = land[sse].groupby("sdwan_bundle").won.mean()
    report["deal_effects"] = {
        "closed_land_deals": int(len(land)),
        "sse_rival_deals": int(sse.sum()),
        "raw_win_sse_no_bundle": round(float(raw_b.get(0, np.nan)), 4),
        "raw_win_sse_bundle": round(float(raw_b.get(1, np.nan)), 4),
        "adj_win_sse_no_bundle": round(cf(sse, bundle=0), 4),
        "adj_win_sse_bundle": round(cf(sse, bundle=1), 4),
        "adj_win_not_aligned": round(cf(land.index == land.index, aligned=0), 4),
        "adj_win_aligned": round(cf(land.index == land.index, aligned=1), 4),
        "adj_win_uncovered": round(cf(land.index == land.index, covered=0), 4),
        "adj_win_covered": round(cf(land.index == land.index, covered=1), 4),
        "note": "Counterfactual averages from a logistic regression of land-deal outcomes on bundle, rival, "
                "bundle x rival, coverage, renewal alignment, partner source, and segment.",
    }

    # ---------------- 5. Prisma Browser ICP ----------------
    b = acc.copy()
    b["contractor_band"] = pd.cut(b.contractor_pct, [0, 0.08, 0.15, 0.25, 1], right=False,
                                  labels=["Under 8%", "8 to 15%", "15 to 25%", "25% or more"]).astype(str)
    b["unmanaged_band"] = pd.cut(b.unmanaged_device_pct, [0, 0.15, 0.25, 0.35, 1], right=False,
                                 labels=["Under 15%", "15 to 25%", "25 to 35%", "35% or more"]).astype(str)
    b["prisma_access"] = np.where(b.has_prisma_access == 1, "Customer", "Not a customer")
    b["vdi"] = np.where(b.vdi_in_use == 1, "Runs VDI", "No VDI")
    attrs = {"prisma_access": "Prisma Access", "contractor_band": "Contractor share",
             "unmanaged_band": "Unmanaged devices", "vdi": "VDI", "industry": "Industry", "segment": "Segment"}
    early = b.browser_early_adopter == 1
    icp_rows, points = [], {}
    for col, label in attrs.items():
        base_share = b[col].value_counts(normalize=True)
        ad_share = b.loc[early, col].value_counts(normalize=True)
        for val, bs in base_share.items():
            ad = float(ad_share.get(val, 0.0))
            lift_v = ad / bs if bs else 0
            pts = int(min(30, 5 * round(max(0.0, 12 * math.log2(lift_v)) / 5))) if lift_v > 0 else 0
            points[(col, val)] = pts
            icp_rows.append({"attribute": label, "value": str(val), "base_share": round(float(bs), 3),
                             "adopter_share": round(ad, 3), "lift": round(lift_v, 2), "points": pts})
    score = np.zeros(len(b), dtype=int)
    for col in attrs:
        score += b[col].map(lambda v, c=col: points.get((c, v), 0)).to_numpy()
    acc["icp_score"] = score
    a_cut, b_cut = np.quantile(score, 0.85), np.quantile(score, 0.55)
    acc["icp_tier"] = np.where(score >= a_cut, "A", np.where(score >= b_cut, "B", "C"))

    # out-of-time validation on post-relaunch Browser deals
    post = opp[(opp.opp_type == "Browser") & (opp.created_date >= pd.Timestamp(C.BROWSER_RELAUNCH))]
    post = post.merge(acc[["account_id", "icp_tier"]], on="account_id")
    tier_val = []
    for t in ["A", "B", "C"]:
        n_acc = int((acc.icp_tier == t).sum())
        p = post[post.icp_tier == t]
        closed = p[p.stage.isin(["Closed Won", "Closed Lost"])]
        tier_val.append({
            "tier": t, "accounts": n_acc,
            "early_adopter_rate": round(float(acc.loc[acc.icp_tier == t, "browser_early_adopter"].mean()), 4),
            "post_launch_opps": int(len(p)),
            "opps_per_100_accounts": round(100 * len(p) / max(n_acc, 1), 1),
            "post_launch_win_rate": round(float((closed.stage == "Closed Won").mean()), 3) if len(closed) else None,
            "post_launch_wins": int((p.stage == "Closed Won").sum()),
        })
    report["icp"] = {"table": icp_rows, "tier_cutoffs": {"A": int(a_cut), "B": int(b_cut)},
                     "tiers": tier_val, "early_adopters": int(early.sum())}

    acc.to_csv(C.DATA_PROCESSED / "accounts_scored.csv", index=False)
    (C.DATA_PROCESSED / "model_report.json").write_text(json.dumps(report, indent=2, default=str))

    m = report["model"]
    print(f"AUC logistic={m['cv_auc_logistic']}  gbm={m['cv_auc_gradient_boosting']}  "
          f"top-decile lift={m['top_decile_lift']}x  top-3-decile capture={m['top3_decile_capture']}")
    print("top drivers:", [(d['driver'], d['coef']) for d in m['drivers'][:6]])
    w = report["whitespace"]
    print(f"whitespace: non-customers={w['non_customers']} land potential=${w['land_potential_total']/1e6:.1f}M "
          f"EV=${w['expected_value_total']/1e6:.1f}M  half of EV in {w['accounts_for_half_of_ev']} accounts "
          f"({w['share_of_accounts_for_half']:.0%})")
    print("coverage gap:", report["coverage_gap"]["by_coverage"],
          "uncovered share of EV", report["coverage_gap"]["uncovered_share_of_ev"])
    print("deal effects:", {k: v for k, v in report["deal_effects"].items() if k != "note"})
    print("ICP tiers:", report["icp"]["tiers"])


if __name__ == "__main__":
    main()
