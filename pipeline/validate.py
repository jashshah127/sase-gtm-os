"""
Data-quality gate between the raw layer and everything downstream.

A revenue number drawn from a bad record is worse than no number, so every
check here either quarantines records (they never reach a metric) or flags
them for owner follow-up (they stay in, but are visible).

Reads  data/raw/*.csv
Writes data/clean/*.csv, data/clean/quarantine_*.csv, data/processed/quality_report.json
"""
from __future__ import annotations

import json
import re

import pandas as pd

import config as C


def normalize_name(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\b(inc|llc|ltd|corp|co)\b\.?", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def main():
    acc = pd.read_csv(C.DATA_RAW / "accounts.csv")
    opp = pd.read_csv(C.DATA_RAW / "opportunities.csv")
    terr = pd.read_csv(C.DATA_RAW / "territories.csv")
    checks = []

    def record(name, description, checked, failed_ids, action, owner):
        checks.append({
            "check": name, "description": description, "rows_checked": int(checked),
            "rows_failed": int(len(failed_ids)), "action": action if len(failed_ids) else "Pass",
            "owner": owner, "sample_ids": list(map(str, failed_ids[:5])),
        })

    # 1. Duplicate accounts (same normalized name, country, and headcount)
    acc["_key"] = acc.account_name.map(normalize_name) + "|" + acc.country + "|" + acc.employees.astype(str)
    acc = acc.sort_values("account_id")
    dup_mask = acc.duplicated("_key", keep="first")
    dup_ids = acc.loc[dup_mask, "account_id"].tolist()
    survivor = acc.drop_duplicates("_key", keep="first").set_index("_key").account_id
    remap = dict(zip(acc.loc[dup_mask, "account_id"], acc.loc[dup_mask, "_key"].map(survivor)))
    record("Duplicate accounts", "Same normalized name, country, and headcount under different IDs",
           len(acc), dup_ids, "Merged into surviving record", "Sales Ops (CRM hygiene)")
    acc_clean = acc.loc[~dup_mask].drop(columns="_key")
    opp["account_id"] = opp.account_id.replace(remap)

    quarantine = []

    # 2. Orphan opportunities
    orphan = ~opp.account_id.isin(acc_clean.account_id)
    record("Orphan opportunities", "Opportunity references an account that does not exist",
           len(opp), opp.loc[orphan, "opp_id"].tolist(), "Quarantined", "Sales Ops (CRM hygiene)")
    quarantine.append(opp.loc[orphan].assign(quarantine_reason="orphan account"))

    # 3. Close date before created date
    created = pd.to_datetime(opp.created_date)
    closed = pd.to_datetime(opp.close_date)
    bad_dates = (closed < created) & ~orphan
    record("Close date before created date", "Impossible lifecycle; usually a data-entry or migration error",
           len(opp), opp.loc[bad_dates, "opp_id"].tolist(), "Quarantined", "Deal owner, via Sales Ops")
    quarantine.append(opp.loc[bad_dates].assign(quarantine_reason="close before create"))

    # 4. Non-positive amounts
    bad_amt = (opp.amount <= 0) & ~orphan & ~bad_dates
    record("Non-positive amount", "Zero or negative ARR on an opportunity",
           len(opp), opp.loc[bad_amt, "opp_id"].tolist(), "Quarantined", "Deal owner, via Sales Ops")
    quarantine.append(opp.loc[bad_amt].assign(quarantine_reason="non-positive amount"))

    keep = ~(orphan | bad_dates | bad_amt)
    opp_clean = opp.loc[keep].copy()

    # 5. Past-due close dates on open deals (flag only)
    is_open = opp_clean.stage.isin(C.OPEN_STAGES)
    past_due = is_open & (pd.to_datetime(opp_clean.close_date) < pd.Timestamp(C.AS_OF))
    record("Past-due close date on open deal", "Open opportunity whose close date has already passed",
           int(is_open.sum()), opp_clean.loc[past_due, "opp_id"].tolist(), "Flagged for owner update",
           "Deal owner")

    # 6. Stage and loss-reason consistency
    lost = opp_clean.stage == "Closed Lost"
    inconsistent = (lost & opp_clean.loss_reason.isna()) | (~lost & opp_clean.loss_reason.notna())
    record("Loss reason consistency", "Closed Lost deals need a loss reason; other stages must not have one",
           len(opp_clean), opp_clean.loc[inconsistent, "opp_id"].tolist(), "Flagged", "Deal owner")

    # 7. Territory referential integrity
    bad_terr = ~acc_clean.territory_id.isin(terr.territory_id)
    record("Territory reference", "Account assigned to a territory that does not exist",
           len(acc_clean), acc_clean.loc[bad_terr, "account_id"].tolist(), "Flagged", "Sales Ops (territory)")

    # 8. Won deals on accounts not marked as customers (logic check)
    won_land = opp_clean[(opp_clean.stage == "Closed Won") & (opp_clean.opp_type == "Land")].account_id
    not_flagged = ~won_land.isin(acc_clean.loc[acc_clean.has_prisma_access == 1, "account_id"])
    record("Won land deal without customer flag", "A closed-won land deal must mark the account as a Prisma Access customer",
           len(won_land), won_land[not_flagged].tolist(), "Flagged", "Sales Ops (CRM hygiene)")

    C.DATA_CLEAN.mkdir(parents=True, exist_ok=True)
    C.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    acc_clean.to_csv(C.DATA_CLEAN / "accounts.csv", index=False)
    opp_clean.to_csv(C.DATA_CLEAN / "opportunities.csv", index=False)
    terr.to_csv(C.DATA_CLEAN / "territories.csv", index=False)
    pd.read_csv(C.DATA_RAW / "specialists.csv").to_csv(C.DATA_CLEAN / "specialists.csv", index=False)
    pd.read_csv(C.DATA_RAW / "launch_enablement_weekly.csv").to_csv(C.DATA_CLEAN / "launch_enablement_weekly.csv", index=False)
    pd.concat(quarantine).to_csv(C.DATA_CLEAN / "quarantine_opportunities.csv", index=False)

    report = {
        "as_of": str(C.AS_OF),
        "raw_accounts": int(len(acc)), "clean_accounts": int(len(acc_clean)),
        "raw_opportunities": int(len(opp)), "clean_opportunities": int(len(opp_clean)),
        "quarantined_opportunities": int((~keep).sum()),
        "checks": checks,
    }
    (C.DATA_PROCESSED / "quality_report.json").write_text(json.dumps(report, indent=2))

    # Self-test: every injected issue must have been caught
    injected = json.loads((C.DATA_RAW / "_injected_issues.json").read_text())
    caught = {
        "duplicate_accounts": set(dup_ids),
        "orphan_opportunities": set(opp.loc[orphan, "opp_id"]),
        "close_before_create": set(opp.loc[bad_dates, "opp_id"]),
        "non_positive_amount": set(opp.loc[bad_amt, "opp_id"]),
        "past_due_close_dates": set(opp_clean.loc[past_due, "opp_id"]),
    }
    for k, ids in injected.items():
        missed = set(ids) - caught[k]
        assert not missed, f"validation missed injected {k}: {sorted(missed)[:5]}"
    for c in checks:
        print(f"  {c['action']:<32} {c['rows_failed']:>4}  {c['check']}")
    print(f"clean accounts={len(acc_clean)} clean opps={len(opp_clean)} quarantined={(~keep).sum()} (all injected issues caught)")


if __name__ == "__main__":
    main()
