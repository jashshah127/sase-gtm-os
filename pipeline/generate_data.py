"""
Synthetic data generator for the SASE GTM Operating System.

Simulates a book of next-generation firewall (NGFW) customers and three years
of SASE sales motion (FY24 Q1 through FY27 Q1-to-date), quarter by quarter:

  * accounts with firmographics, incumbents, renewal dates, and territories
  * core territories and SASE specialist overlay coverage
  * land opportunities (first Prisma Access purchase), expansions, and
    Prisma Browser opportunities, each with a full lifecycle
  * weekly Prisma Browser launch enablement data

The generating process deliberately contains patterns for the analysis to
find (coverage effects, competitive dynamics, renewal timing). They are
documented in docs/methodology.md so nothing is hidden from a reviewer.

ALL DATA IS SYNTHETIC. No real customer, deal, or employee data is used.
Run:  python pipeline/generate_data.py
"""
from __future__ import annotations

import json
import math
from datetime import date, timedelta

import numpy as np
import pandas as pd

import config as C

rng = np.random.default_rng(C.SEED)
rng_ph = np.random.default_rng(C.SEED + 1)   # placeholder close dates only; keeps the main stream stable


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def add_days(d: date, n) -> date:
    return d + timedelta(days=int(round(float(n))))


# ---------------------------------------------------------------------------
# Fictional names (coined words, so they don't collide with real companies)
# ---------------------------------------------------------------------------
SYL_START = ["Al", "Bel", "Cor", "Dar", "El", "Fen", "Gal", "Hal", "Il", "Jor", "Kel", "Lor",
             "Mar", "Nor", "Or", "Pel", "Quin", "Ros", "Sol", "Tor", "Val", "Wen", "Zel", "Bra",
             "Cal", "Dor", "Ev", "Fal", "Gren", "Hav", "Kor", "Lum", "Mer", "Nev", "Ost", "Pry",
             "Rav", "Sev", "Tal", "Ul", "Ver", "Wyn", "Yar", "Ash", "Brin", "Cres", "Del", "Ems"]
SYL_MID = ["a", "e", "i", "o", "ar", "en", "is", "on", "ur", "el", "an", ""]
SYL_END = ["ton", "mark", "via", "ex", "ora", "wick", "dale", "gate", "field", "crest", "line",
           "ridge", "stone", "vale", "bridge", "port", "haven", "wood", "more", "ley", "stead",
           "brook", "mont", "shire", "well", "forth"]
SUFFIX = {
    "Financial Services": ["Bank", "Financial", "Capital", "Credit Union", "Insurance", "Asset Management"],
    "Healthcare": ["Health", "Medical Group", "Health System", "Clinics", "Life Sciences"],
    "Manufacturing": ["Manufacturing", "Industries", "Components", "Motors", "Materials"],
    "Retail": ["Retail", "Stores", "Brands", "Outfitters", "Markets"],
    "Technology": ["Software", "Systems", "Labs", "Technologies", "Cloud"],
    "Public Sector": ["County Government", "Transit Authority", "Water District", "Port Authority",
                      "Public Health Agency"],
    "Energy & Utilities": ["Energy", "Power", "Utilities", "Renewables"],
    "Professional Services": ["Partners", "Consulting", "Advisory", "Legal LLP", "Group"],
    "Education": ["University", "College", "School District", "Institute of Technology"],
    "Telecommunications": ["Telecom", "Networks", "Communications", "Mobile"],
}
FIRST_NAMES = ["Aisha", "Ben", "Carmen", "Daniel", "Elena", "Farhan", "Grace", "Hiro", "Isabel",
               "Jonas", "Kavya", "Liam", "Maya", "Noah", "Olivia", "Priya", "Quentin", "Rosa",
               "Samuel", "Tara", "Umar", "Valentina", "Wei", "Ximena", "Yusuf", "Zoe", "Arjun",
               "Bianca", "Chen", "Diego", "Emeka", "Fatima", "Gabriel", "Hana", "Ivan", "Julia",
               "Kenji", "Leila", "Marco", "Nadia", "Oscar", "Paula", "Rahul", "Sofia", "Tomas"]
LAST_NAMES = ["Adeyemi", "Brennan", "Castillo", "Dubois", "Eriksen", "Fischer", "Gupta", "Haddad",
              "Ito", "Jensen", "Kowalski", "Lindqvist", "Moreau", "Nakamura", "Okafor", "Park",
              "Quinn", "Rossi", "Silva", "Tanaka", "Umeh", "Varga", "Whitfield", "Xu", "Yamamoto",
              "Zimmerman", "Alvarez", "Bose", "Chandra", "Delgado", "Evans", "Farouk", "Greco",
              "Holm", "Iyer", "Jovanovic", "Kim", "Laurent", "Mehta", "Novak", "Ortiz", "Petrov"]

SEG_CODE = {"Large Enterprise": "LE", "Enterprise": "ENT", "Mid-Market": "MM", "Commercial": "COM"}


def make_account_names(industries):
    used, out = set(), []
    for ind in industries:
        for _ in range(500):
            base = (rng.choice(SYL_START) + rng.choice(SYL_MID) + rng.choice(SYL_END)).capitalize()
            name = f"{base} {rng.choice(SUFFIX[ind])}"
            if name not in used:
                used.add(name)
                out.append(name)
                break
        else:  # extremely unlikely fallback
            out.append(f"{base} {ind} {len(out)}")
    return out


def log_uniform(lo, hi, n):
    return np.exp(rng.uniform(np.log(lo), np.log(hi), n))


# ---------------------------------------------------------------------------
# 1. Accounts
# ---------------------------------------------------------------------------
def build_accounts():
    N = C.N_ACCOUNTS
    seg = rng.choice(C.SEGMENTS, N, p=C.SEGMENT_MIX)
    region = rng.choice(C.REGIONS, N, p=C.REGION_MIX)
    industry = rng.choice(C.INDUSTRIES, N, p=C.INDUSTRY_MIX)
    country = np.array([rng.choice(C.COUNTRIES[r][0], p=C.COUNTRIES[r][1]) for r in region])

    emp = np.zeros(N)
    m = seg == "Large Enterprise"
    emp[m] = np.clip(np.exp(rng.normal(np.log(22000), 0.55, m.sum())), 10000, 250000)
    m = seg == "Enterprise"
    emp[m] = log_uniform(2000, 10000, m.sum())
    m = seg == "Mid-Market"
    emp[m] = log_uniform(500, 2000, m.sum())
    m = seg == "Commercial"
    emp[m] = log_uniform(100, 500, m.sum())
    emp = (np.round(emp / 10) * 10).astype(int)

    br_med = {"Large Enterprise": 120, "Enterprise": 30, "Mid-Market": 9, "Commercial": 3}
    br_clip = {"Large Enterprise": (20, 900), "Enterprise": (5, 220), "Mid-Market": (2, 45), "Commercial": (1, 12)}
    ind_br = {"Retail": 2.0, "Financial Services": 1.5, "Healthcare": 1.4, "Public Sector": 1.2,
              "Education": 1.1, "Technology": 0.6, "Professional Services": 0.8, "Manufacturing": 1.0,
              "Energy & Utilities": 1.2, "Telecommunications": 1.3}
    branches = np.array([
        int(np.clip(np.exp(rng.normal(np.log(br_med[s] * ind_br[i]), 0.55)), *br_clip[s]))
        for s, i in zip(seg, industry)])

    ind_remote = {"Technology": 0.55, "Professional Services": 0.50, "Financial Services": 0.40,
                  "Telecommunications": 0.38, "Healthcare": 0.25, "Education": 0.30, "Public Sector": 0.28,
                  "Manufacturing": 0.18, "Retail": 0.15, "Energy & Utilities": 0.20}
    remote = np.clip(np.array([ind_remote[i] for i in industry]) + rng.normal(0, 0.08, N), 0.05, 0.85)

    ind_contract = {"Technology": 0.18, "Professional Services": 0.16, "Healthcare": 0.15,
                    "Financial Services": 0.14, "Telecommunications": 0.12, "Manufacturing": 0.10,
                    "Retail": 0.08, "Energy & Utilities": 0.12, "Public Sector": 0.08, "Education": 0.06}
    seg_contract = {"Large Enterprise": 1.3, "Enterprise": 1.1, "Mid-Market": 0.9, "Commercial": 0.7}
    contractor = np.clip(np.array([ind_contract[i] * seg_contract[s] for i, s in zip(industry, seg)])
                         + rng.normal(0, 0.04, N), 0.01, 0.45)

    unmanaged = 0.12 + 0.45 * contractor + rng.normal(0, 0.05, N)
    unmanaged += np.where(industry == "Education", 0.15, 0) + np.where(industry == "Healthcare", 0.05, 0)
    unmanaged = np.clip(unmanaged, 0.03, 0.60)

    big = np.isin(seg, ["Large Enterprise", "Enterprise"]).astype(float)
    regulated = np.isin(industry, ["Financial Services", "Healthcare", "Public Sector"]).astype(float)
    vdi = (rng.random(N) < sigmoid(-1.6 + 1.0 * big + 0.8 * regulated + 3.0 * contractor)).astype(int)

    inc_p = {"Large Enterprise": [0.34, 0.14, 0.26, 0.09, 0.08, 0.04, 0.05],
             "Enterprise": [0.42, 0.18, 0.18, 0.08, 0.06, 0.03, 0.05],
             "Mid-Market": [0.50, 0.22, 0.10, 0.05, 0.05, 0.03, 0.05],
             "Commercial": [0.54, 0.26, 0.06, 0.03, 0.04, 0.02, 0.05]}
    incumbent = np.array([rng.choice(C.INCUMBENTS, p=inc_p[s]) for s in seg])

    xdr_p = {"Large Enterprise": 0.45, "Enterprise": 0.30, "Mid-Market": 0.18, "Commercial": 0.08}
    cloud_p = {"Large Enterprise": 0.35, "Enterprise": 0.22, "Mid-Market": 0.10, "Commercial": 0.04}
    cortex_xdr = (rng.random(N) < np.array([xdr_p[s] for s in seg])).astype(int)
    cortex_cloud = (rng.random(N) < np.array([cloud_p[s] for s in seg])).astype(int)
    health = np.clip(rng.normal(72, 12, N), 20, 99).round().astype(int)

    since = np.where(big == 1, rng.integers(2008, 2021, N), rng.integers(2010, 2025, N))

    rate = np.exp(rng.normal(np.log(45), 0.35, N))
    rate *= np.select([seg == "Large Enterprise", seg == "Commercial"], [0.8, 1.4], 1.0)
    ngfw_arr = (np.round(emp * rate / 100) * 100).astype(int)

    term_m = np.select([big == 1, seg == "Mid-Market"], [36, 24], 12)
    next_renewal = [add_days(C.AS_OF, rng.integers(10, t * 30.4)) for t in term_m]

    names = make_account_names(industry)

    df = pd.DataFrame({
        "account_id": [f"A{100000 + i}" for i in range(N)],
        "account_name": names,
        "industry": industry, "segment": seg, "region": region, "country": country,
        "employees": emp, "branch_count": branches,
        "remote_workforce_pct": remote.round(3), "contractor_pct": contractor.round(3),
        "unmanaged_device_pct": unmanaged.round(3), "vdi_in_use": vdi,
        "incumbent_remote_access": incumbent,
        "cortex_xdr": cortex_xdr, "cortex_cloud": cortex_cloud, "health_score": health,
        "customer_since": since, "ngfw_arr": ngfw_arr,
        "ngfw_renewal_date": next_renewal, "renewal_term_months": term_m,
    })
    # Potential sizing (see config for pricing assumptions)
    df["mobile_users"] = np.round(df.employees * np.minimum(0.95, 0.35 + df.remote_workforce_pct)).astype(int)
    price = df.segment.map(C.PRICE_PER_USER)
    df["full_potential_arr"] = (df.mobile_users * price + df.branch_count * C.PRICE_PER_BRANCH).round(-2)
    df["land_potential_arr"] = (df.full_potential_arr * df.segment.map(C.LAND_SHARE)).round(-2)
    return df


# ---------------------------------------------------------------------------
# 2. Territories and specialist coverage
# ---------------------------------------------------------------------------
def build_territories(acc: pd.DataFrame):
    terr_rows, spec_rows = [], []
    acc["territory_id"] = ""
    for r in C.REGIONS:
        for s in C.SEGMENTS:
            idx = acc.index[(acc.region == r) & (acc.segment == s)].to_numpy()
            if len(idx) == 0:
                continue
            n_t = max(1, round(len(idx) / C.ACCOUNTS_PER_CORE_TERRITORY[s]))
            weights = rng.dirichlet(np.ones(n_t) * 6)            # mild natural imbalance
            assign = rng.choice(n_t, len(idx), p=weights)
            n_cov = round(n_t * C.SPECIALIST_COVERAGE[(r, s)])
            covered = set(rng.choice(n_t, n_cov, replace=False).tolist()) if n_cov else set()
            tids = [f"{r}-{SEG_CODE[s]}-{t + 1:02d}" for t in range(n_t)]
            acc.loc[idx, "territory_id"] = [tids[a] for a in assign]
            sizes = np.bincount(assign, minlength=n_t)

            # specialists for the covered territories
            cov_accounts = int(sum(sizes[t] for t in covered))
            n_sp = math.ceil(cov_accounts / C.ACCOUNTS_PER_SPECIALIST[s]) if cov_accounts else 0
            sp_ids = []
            for k in range(n_sp):
                sp_id = f"SP-{len(spec_rows) + 1:03d}"
                recent = rng.random() < 0.18
                hire = (add_days(date(2025, 7, 1), rng.integers(0, 410)) if recent
                        else add_days(date(2019, 1, 1), rng.integers(0, 2372)))
                spec_rows.append({
                    "specialist_id": sp_id,
                    "specialist_name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                    "region": r, "segment": s, "hire_date": hire,
                })
                sp_ids.append(sp_id)
            cov_sorted = sorted(covered, key=lambda t: -sizes[t])
            owner = {t: sp_ids[j % n_sp] for j, t in enumerate(cov_sorted)} if n_sp else {}
            for t in range(n_t):
                terr_rows.append({
                    "territory_id": tids[t], "region": r, "segment": s,
                    "account_count": int(sizes[t]),
                    "specialist_covered": int(t in covered),
                    "specialist_id": owner.get(t, ""),
                })
    terr = pd.DataFrame(terr_rows)
    spec = pd.DataFrame(spec_rows)
    acc["specialist_covered"] = acc.territory_id.map(terr.set_index("territory_id").specialist_covered).astype(int)
    return terr, spec


# ---------------------------------------------------------------------------
# 3. Fit (demand) score used by the simulation. Region and coverage are NOT
#    part of fit: coverage is a go-to-market choice, not customer demand.
# ---------------------------------------------------------------------------
SEG_FIT = {"Large Enterprise": 0.9, "Enterprise": 0.5, "Mid-Market": 0.0, "Commercial": -0.6}
IND_FIT = {"Financial Services": 0.45, "Healthcare": 0.35, "Technology": 0.40,
           "Professional Services": 0.25, "Telecommunications": 0.15, "Retail": 0.05,
           "Manufacturing": -0.15, "Energy & Utilities": -0.10, "Public Sector": -0.30, "Education": -0.20}
INC_FIT = {"GlobalProtect VPN": 0.55, "Third-party VPN": 0.15, "Zscaler": -1.1, "Netskope": -0.8,
           "Cisco": -0.4, "Cloudflare": -0.5, "Fortinet": -0.3}
BR_MED = {"Large Enterprise": 120, "Enterprise": 30, "Mid-Market": 9, "Commercial": 3}


def fit_logit(acc):
    return (-2.2 + acc.segment.map(SEG_FIT) + acc.industry.map(IND_FIT)
            + 2.2 * (acc.remote_workforce_pct - 0.30)
            + 0.35 * np.log(acc.branch_count / acc.segment.map(BR_MED))
            + 1.8 * (acc.contractor_pct - 0.12)
            + 0.35 * acc.cortex_xdr + 0.30 * acc.cortex_cloud
            + 0.015 * (acc.health_score - 72)
            + acc.incumbent_remote_access.map(INC_FIT)).to_numpy()


# ---------------------------------------------------------------------------
# 4. Deal lifecycle helpers
# ---------------------------------------------------------------------------
# Simulation calibration knobs
HIST_OFFSET = -1.10     # intercept shift for pre-window adopters
LAND_C0 = -2.80         # base quarterly land-opportunity creation logit
LAND_TREND = 0.11       # quarterly growth in land-opportunity creation
EXP_C0 = -3.30          # base quarterly expansion-opportunity logit
HIST_ARR_SHARE = (0.20, 0.50)

BASE_WIN = {"Large Enterprise": 0.18, "Enterprise": 0.20, "Mid-Market": 0.22, "Commercial": 0.24}
COMP_WIN = {"No competitor": 0.22, "Zscaler": -0.12, "Netskope": -0.07, "Cisco": 0.04,
            "Fortinet": 0.0, "Cloudflare": -0.03}
BASE_CYCLE = {"Large Enterprise": (190, 50), "Enterprise": (140, 40), "Mid-Market": (100, 30), "Commercial": (65, 20)}
STAGE_CUTS = [0.18, 0.38, 0.65, 0.85]        # share of cycle elapsed when each next stage begins
LOSS_POINT = {"Qualify": 0.35, "Technical Validation": 0.60, "Proposal": 0.80, "Negotiation": 0.95}


def renewal_after(next_renewal: date, term_months: int, d: date) -> date:
    term_days = int(round(term_months * 30.4))
    k = (next_renewal - d).days // term_days
    return next_renewal - timedelta(days=k * term_days)


def pick_loss(comp: str, opp_type: str):
    if opp_type != "Land":
        stage = rng.choice(["Qualify", "Technical Validation", "Proposal", "Negotiation"], p=[0.30, 0.35, 0.22, 0.13])
        reason = rng.choice(["Timing or budget", "Price", "No decision", "POV outcome"], p=[0.35, 0.25, 0.25, 0.15])
        return stage, reason
    if comp in ("Zscaler", "Netskope"):
        stage = rng.choice(["Qualify", "Technical Validation", "Proposal", "Negotiation"], p=[0.15, 0.50, 0.20, 0.15])
    elif comp == "No competitor":
        stage = rng.choice(["Qualify", "Technical Validation", "Proposal", "Negotiation"], p=[0.40, 0.25, 0.20, 0.15])
    else:
        stage = rng.choice(["Qualify", "Technical Validation", "Proposal", "Negotiation"], p=[0.25, 0.40, 0.20, 0.15])
    if comp == "No competitor":
        reason = rng.choice(["No decision", "Timing or budget", "Price"], p=[0.5, 0.3, 0.2])
    elif stage == "Technical Validation":
        reason = rng.choice(["POV outcome", "Chose competitor", "Incumbent contract term"], p=[0.45, 0.35, 0.20])
    elif stage in ("Proposal", "Negotiation"):
        reason = rng.choice(["Price", "Chose competitor", "Timing or budget"], p=[0.40, 0.40, 0.20])
    else:
        reason = rng.choice(["No decision", "Incumbent contract term", "Timing or budget"], p=[0.4, 0.3, 0.3])
    return stage, reason


def lifecycle(created: date, cycle: float, fate_won: bool, loss_stage: str | None, stall_prone: bool,
              placeholder_p: float = 0.0):
    """Resolve close date, pushes, current stage and stage-entry date as of C.AS_OF.

    Always consumes exactly six draws from the main generator so that changes to
    one deal's path never shift the random stream for every deal after it.
    Deals still open at the as-of date may carry a rep-entered placeholder close
    date at a later quarter end (drawn from a separate generator).
    """
    u = rng.random(6)
    span = cycle if fate_won else cycle * LOSS_POINT[loss_stage]
    if placeholder_p and add_days(created, span) > C.AS_OF and rng_ph.random() < placeholder_p:
        span += rng_ph.uniform(60, 220)
    close = add_days(created, max(10, span))
    pushes, last_push = 0, None
    if u[0] < 0.34:
        n_push = 1 if u[1] < 0.6 else (2 if u[1] < 0.9 else 3)
        for k in range(n_push):
            push_day = add_days(close, -5)
            if push_day > C.AS_OF:
                break
            pushes += 1
            last_push = push_day
            close = add_days(close, 14 + int(u[2 + k] * 36))
    if close <= C.AS_OF:
        stage = "Closed Won" if fate_won else "Closed Lost"
        return dict(close=close, stage=stage, pushes=pushes, last_push=last_push, stage_entry=close)
    total = (close - created).days
    progress = (C.AS_OF - created).days / max(total, 1)
    k = int(np.searchsorted(STAGE_CUTS, progress, side="right"))
    if not fate_won:
        k = min(k, C.OPEN_STAGES.index(loss_stage))
    stage = C.OPEN_STAGES[k]
    start_frac = 0.0 if k == 0 else STAGE_CUTS[k - 1]
    entry = add_days(created, total * start_frac)
    if entry > C.AS_OF:
        entry = C.AS_OF
    if stage == "Technical Validation" and stall_prone:
        entry = max(add_days(created, 5), add_days(C.AS_OF, -(60 + int(u[5] * 80))))
    return dict(close=close, stage=stage, pushes=pushes, last_push=last_push, stage_entry=entry)


# ---------------------------------------------------------------------------
# 5. Simulation of the SASE sales motion
# ---------------------------------------------------------------------------
def simulate(acc: pd.DataFrame):
    N = len(acc)
    fit = fit_logit(acc)
    fit_mean = fit.mean()
    cov = acc.specialist_covered.to_numpy()
    seg = acc.segment.to_numpy()
    inc = acc.incumbent_remote_access.to_numpy()
    br = acc.branch_count.to_numpy()
    users = acc.mobile_users.to_numpy()
    full_pot = acc.full_potential_arr.to_numpy()
    next_ren = acc.ngfw_renewal_date.to_numpy()
    term = acc.renewal_term_months.to_numpy()
    big = np.isin(seg, ["Large Enterprise", "Enterprise"])

    adopted = [None] * N
    sdwan = np.zeros(N, dtype=int)
    arr = np.zeros(N)
    open_until = [date.min] * N
    cooldown = [date.min] * N
    exp_open_until = [date.min] * N

    # Historical adopters (bought Prisma Access before the simulation window)
    p_hist = sigmoid(fit + 0.9 * cov + HIST_OFFSET)
    hist = rng.random(N) < p_hist
    for i in np.where(hist)[0]:
        adopted[i] = add_days(date(2020, 1, 1), rng.integers(0, 1126))
        sdwan[i] = int(rng.random() < sigmoid(-1.2 + 0.5 * np.log(br[i] / BR_MED[seg[i]]) + 0.6 * cov[i]))
        arr[i] = round(full_pot[i] * rng.uniform(*HIST_ARR_SHARE), -2)

    quarters = [(2023, 3), (2023, 4)] + [(fy, q) for fy in (2024, 2025, 2026) for q in (1, 2, 3, 4)] + [(2027, 1)]
    opps = []

    for qi, (fy, q) in enumerate(quarters):
        qs, qe = C.quarter_bounds(fy, q)
        if qs > C.AS_OF:
            break
        qe_eff = min(qe, C.AS_OF)
        frac = ((qe_eff - qs).days + 1) / ((qe - qs).days + 1)
        trend = LAND_TREND * qi

        # ---- Land opportunities
        for i in range(N):
            if adopted[i] is not None or open_until[i] >= qs or cooldown[i] >= qs:
                continue
            if rng.random() >= sigmoid(fit[i] + 0.95 * cov[i] + trend + LAND_C0) * frac:
                continue
            created = add_days(qs, rng.integers(0, (qe_eff - qs).days + 1))
            comp = inc[i] if inc[i] in C.SSE_COMPETITORS else rng.choice(
                C.COMPETITORS, p=[0.36, 0.14, 0.14, 0.10, 0.07, 0.19])
            b_logit = (-1.1 + 0.05 * qi + 0.55 * np.log(br[i] / BR_MED[seg[i]]) + 0.35 * big[i] + 0.6 * cov[i])
            bundle = int(rng.random() < sigmoid(b_logit))
            src_p = [0.30, 0.35, 0.20, 0.15] if cov[i] else [0.50, 0.0, 0.30, 0.20]
            if seg[i] in ("Mid-Market", "Commercial"):
                src_p = [src_p[0] - 0.10, src_p[1], src_p[2] + 0.10, src_p[3]]
            src = rng.choice(C.SOURCES, p=src_p)
            mu, sd = BASE_CYCLE[seg[i]]
            cycle = max(25, rng.normal(mu, sd)) + (25 if comp == "Zscaler" else 0) + (15 if bundle else 0)
            ren = renewal_after(next_ren[i], term[i], created)
            aligned = int(90 <= (ren - created).days <= 270)
            wp = (BASE_WIN[seg[i]] + COMP_WIN[comp]
                  + ((0.14 if comp in ("Zscaler", "Netskope") else 0.03) if bundle else 0)
                  + (0.06 if src == "Partner-sourced" and seg[i] in ("Mid-Market", "Commercial") else 0)
                  + 0.10 * aligned + 0.08 * cov[i] + 0.06 * (fit[i] - fit_mean))
            won = rng.random() < float(np.clip(wp, 0.05, 0.88))
            loss_stage, loss_reason = (None, None) if won else pick_loss(comp, "Land")
            base_amt = users[i] * C.PRICE_PER_USER[seg[i]] + (br[i] * C.PRICE_PER_BRANCH if bundle else 0)
            amount = round(base_amt * C.LAND_SHARE[seg[i]] * rng.lognormal(0, 0.25), -2)
            lc = lifecycle(created, cycle, won, loss_stage, stall_prone=rng.random() < 0.30, placeholder_p=0.5)
            opps.append(dict(account_idx=i, opp_type="Land",
                             product="Prisma SASE bundle" if bundle else "Prisma Access",
                             created_date=created, close_date=lc["close"], stage=lc["stage"],
                             amount=max(amount, 3000.0), competitor=comp, sdwan_bundle=bundle, source=src,
                             loss_reason=loss_reason if lc["stage"] == "Closed Lost" else None,
                             loss_stage=loss_stage if lc["stage"] == "Closed Lost" else None,
                             stage_entry_date=lc["stage_entry"], push_count=lc["pushes"],
                             last_push_date=lc["last_push"], renewal_aligned=aligned,
                             cycle_days=cycle, fate_won=won))
            open_until[i] = lc["close"]
            if won:
                adopted[i] = lc["close"]
                if lc["close"] <= C.AS_OF:
                    arr[i] = opps[-1]["amount"]
                    sdwan[i] = max(sdwan[i], bundle)
            else:
                cooldown[i] = add_days(lc["close"], 270)

        # ---- Expansion opportunities for existing Prisma Access customers
        for i in range(N):
            if adopted[i] is None or adopted[i] > add_days(qs, -120) or exp_open_until[i] >= qs:
                continue
            p = sigmoid(EXP_C0 + 0.5 * cov[i] + 0.08 * qi + 0.3 * big[i]) * frac
            if rng.random() >= p:
                continue
            created = add_days(qs, rng.integers(0, (qe_eff - qs).days + 1))
            if not sdwan[i] and rng.random() < 0.5:
                product = "SD-WAN add-on"
                amount = round(br[i] * C.PRICE_PER_BRANCH * rng.uniform(0.5, 1.0), -2)
            else:
                product = "Seat expansion"
                amount = round(max(5000, (full_pot[i] - arr[i]) * rng.uniform(0.15, 0.35)), -2)
            cycle = rng.uniform(40, 110)
            won = rng.random() < 0.58 + 0.08 * cov[i]
            loss_stage, loss_reason = (None, None) if won else pick_loss("", "Expansion")
            lc = lifecycle(created, cycle, won, loss_stage, stall_prone=False, placeholder_p=0.4)
            opps.append(dict(account_idx=i, opp_type="Expansion", product=product,
                             created_date=created, close_date=lc["close"], stage=lc["stage"],
                             amount=float(amount), competitor="No competitor", sdwan_bundle=int(product == "SD-WAN add-on"),
                             source="Specialist-sourced" if cov[i] else "AE-sourced",
                             loss_reason=loss_reason if lc["stage"] == "Closed Lost" else None,
                             loss_stage=loss_stage if lc["stage"] == "Closed Lost" else None,
                             stage_entry_date=lc["stage_entry"], push_count=lc["pushes"],
                             last_push_date=lc["last_push"], renewal_aligned=0,
                             cycle_days=cycle, fate_won=won))
            exp_open_until[i] = lc["close"]
            if won and lc["close"] <= C.AS_OF:
                arr[i] = min(arr[i] + amount, full_pot[i] * 1.1)
                if product == "SD-WAN add-on":
                    sdwan[i] = 1

    has_sase = np.array([a is not None and a <= C.AS_OF for a in adopted]).astype(int)
    acc["has_prisma_access"] = has_sase
    acc["has_prisma_sdwan"] = np.where(has_sase == 1, sdwan, 0)
    acc["sase_first_purchase_date"] = [a if (a is not None and a <= C.AS_OF) else None for a in adopted]
    acc["sase_arr"] = np.where(has_sase == 1, np.round(arr, -2), 0)
    return opps


# ---------------------------------------------------------------------------
# 6. Prisma Browser: early adopters, post-relaunch pipeline, enablement
# ---------------------------------------------------------------------------
BROWSER_INDUSTRIES = ["Financial Services", "Healthcare", "Professional Services", "Technology"]


def browser_fit(acc, has_sase_flag):
    return (-4.6 + 3.2 * acc.contractor_pct + 2.2 * acc.unmanaged_device_pct + 0.9 * acc.vdi_in_use
            + 0.55 * acc.industry.isin(BROWSER_INDUSTRIES) + 1.3 * has_sase_flag
            + 0.35 * acc.segment.isin(["Large Enterprise", "Enterprise"]) + 0.25 * acc.specialist_covered).to_numpy()


def simulate_browser(acc: pd.DataFrame, opps: list):
    N = len(acc)
    first = pd.to_datetime(acc.sase_first_purchase_date)
    sase_by_2025 = (first.notna() & (first <= pd.Timestamp("2025-06-30"))).astype(int).to_numpy()
    bfit = browser_fit(acc, sase_by_2025)
    emp = acc.employees.to_numpy()
    con = acc.contractor_pct.to_numpy()
    unm = acc.unmanaged_device_pct.to_numpy()
    has_sase_now = acc.has_prisma_access.to_numpy()

    def amount_for(i):
        return round(max(6000, emp[i] * (con[i] + 0.5 * unm[i]) * C.BROWSER_PRICE_PER_USER * rng.lognormal(0, 0.2)), -2)

    browser = np.zeros(N, dtype=int)
    browser_arr = np.zeros(N)

    # Early adopters, before the March 2026 relaunch
    p_early = sigmoid(bfit + 0.55)
    early = np.where(rng.random(N) < p_early * 0.16)[0]
    for i in early:
        close = add_days(date(2024, 6, 1), rng.integers(0, 650))
        cycle = rng.uniform(50, 120)
        created = add_days(close, -cycle)
        browser[i] = 1
        browser_arr[i] = amount_for(i)
        opps.append(dict(account_idx=i, opp_type="Browser", product="Prisma Browser",
                         created_date=created, close_date=close, stage="Closed Won",
                         amount=float(browser_arr[i]), competitor="No competitor", sdwan_bundle=0,
                         source="Specialist-sourced" if acc.specialist_covered.iat[i] else "AE-sourced",
                         loss_reason=None, loss_stage=None, stage_entry_date=close, push_count=0,
                         last_push_date=None, renewal_aligned=0, cycle_days=cycle, fate_won=True))
    # A matching set of early losses so win rates are not trivially 100%
    others = np.setdiff1d(np.arange(N), early)
    w = np.exp(bfit[others])
    lost_idx = rng.choice(others, size=int(len(early) * 0.8), replace=False, p=w / w.sum())
    for i in lost_idx:
        close = add_days(date(2024, 6, 1), rng.integers(0, 650))
        cycle = rng.uniform(40, 110)
        stage, reason = pick_loss("", "Expansion")
        opps.append(dict(account_idx=int(i), opp_type="Browser", product="Prisma Browser",
                         created_date=add_days(close, -cycle), close_date=close, stage="Closed Lost",
                         amount=float(amount_for(i)), competitor="No competitor", sdwan_bundle=0,
                         source="AE-sourced", loss_reason=reason, loss_stage=stage, stage_entry_date=close,
                         push_count=0, last_push_date=None, renewal_aligned=0, cycle_days=cycle, fate_won=False))

    # Post-relaunch weekly pipeline creation
    z = (bfit - bfit.mean()) / bfit.std()
    open_browser = set()
    n_weeks = (C.AS_OF - C.BROWSER_RELAUNCH).days // 7 + 1
    for wk in range(n_weeks):
        wk_start = add_days(C.BROWSER_RELAUNCH, 7 * wk)
        n_new = rng.poisson(5 + 13 * (1 - math.exp(-wk / 5)))
        eligible = np.array([i for i in range(N) if not browser[i] and i not in open_browser])
        if len(eligible) == 0 or n_new == 0:
            continue
        ww = np.exp(bfit[eligible] + rng.normal(0, 0.3, len(eligible)))
        chosen = rng.choice(eligible, size=min(n_new, len(eligible)), replace=False, p=ww / ww.sum())
        for i in chosen:
            created = add_days(wk_start, rng.integers(0, 7))
            if created > C.AS_OF:
                continue
            cycle = float(np.clip(rng.normal(75, 20), 30, 150))
            wp = float(np.clip(0.22 + 0.10 * z[i] + 0.12 * has_sase_now[i], 0.06, 0.75))
            won = rng.random() < wp
            loss_stage = loss_reason = None
            if not won:
                loss_stage = rng.choice(["Qualify", "Technical Validation", "Proposal", "Negotiation"], p=[0.25, 0.50, 0.15, 0.10])
                loss_reason = rng.choice(["POV outcome", "No decision", "Price", "Timing or budget"], p=[0.40, 0.25, 0.20, 0.15])
            lc = lifecycle(created, cycle, won, loss_stage, stall_prone=rng.random() < 0.35)
            amt = amount_for(i)
            opps.append(dict(account_idx=int(i), opp_type="Browser", product="Prisma Browser",
                             created_date=created, close_date=lc["close"], stage=lc["stage"],
                             amount=float(amt), competitor="No competitor", sdwan_bundle=0,
                             source=rng.choice(C.SOURCES, p=[0.35, 0.30, 0.15, 0.20]),
                             loss_reason=loss_reason if lc["stage"] == "Closed Lost" else None,
                             loss_stage=loss_stage if lc["stage"] == "Closed Lost" else None,
                             stage_entry_date=lc["stage_entry"], push_count=lc["pushes"],
                             last_push_date=lc["last_push"], renewal_aligned=0, cycle_days=cycle, fate_won=won))
            open_browser.add(int(i))
            if won and lc["close"] <= C.AS_OF:
                browser[i] = 1
                browser_arr[i] = amt

    acc["has_prisma_browser"] = browser
    acc["browser_arr"] = np.round(browser_arr, -2)
    acc["browser_early_adopter"] = 0
    acc.loc[early, "browser_early_adopter"] = 1


def enablement_series():
    """Weekly share of field sellers certified on the Prisma Browser launch, by region."""
    n_weeks = (C.AS_OF - C.BROWSER_RELAUNCH).days // 7 + 1
    finals = {"AMER": 0.88, "EMEA": 0.81, "JAPAC": 0.61}
    speeds = {"AMER": 4.0, "EMEA": 5.0, "JAPAC": 8.0}
    heads = {"AMER": 420, "EMEA": 260, "JAPAC": 170}
    rows = []
    for r in C.REGIONS:
        for wk in range(n_weeks):
            pct = finals[r] * (1 - math.exp(-(wk + 1) / speeds[r])) + rng.normal(0, 0.006)
            rows.append({"week_start": add_days(C.BROWSER_RELAUNCH, 7 * wk), "region": r,
                         "field_headcount": heads[r], "certified_pct": round(float(np.clip(pct, 0, 0.99)), 3)})
    df = pd.DataFrame(rows)
    df["certified_pct"] = df.groupby("region").certified_pct.cummax()   # certification never goes backwards
    return df


# ---------------------------------------------------------------------------
# 7. Data-quality issues injected into the RAW layer (validate.py must catch them)
# ---------------------------------------------------------------------------
def inject_quality_issues(acc: pd.DataFrame, opp: pd.DataFrame):
    injected = {}
    dup_src = acc.sample(9, random_state=7)
    dups = dup_src.copy()
    dups["account_id"] = [f"A{900000 + k}" for k in range(len(dups))]
    dups["account_name"] = dups.account_name.str.upper() + " INC"
    acc_raw = pd.concat([acc, dups], ignore_index=True)
    injected["duplicate_accounts"] = dups.account_id.tolist()

    opp_raw = opp.copy()
    closed = opp_raw.index[opp_raw.stage.isin(["Closed Won", "Closed Lost"])]
    swap = rng.choice(closed, 14, replace=False)
    opp_raw.loc[swap, ["created_date", "close_date"]] = opp_raw.loc[swap, ["close_date", "created_date"]].to_numpy()
    injected["close_before_create"] = opp_raw.loc[swap, "opp_id"].tolist()

    remaining = np.setdiff1d(opp_raw.index, swap)
    bad_amt = rng.choice(remaining, 6, replace=False)
    opp_raw.loc[bad_amt, "amount"] = [0, -12500, 0, -4800, 0, -900]
    injected["non_positive_amount"] = opp_raw.loc[bad_amt, "opp_id"].tolist()

    orphans = opp_raw.sample(11, random_state=11).copy()
    orphans["opp_id"] = [f"O{990000 + k}" for k in range(len(orphans))]
    orphans["account_id"] = [f"A{800000 + k}" for k in range(len(orphans))]
    opp_raw = pd.concat([opp_raw, orphans], ignore_index=True)
    injected["orphan_opportunities"] = orphans.opp_id.tolist()

    # Hygiene flag (not quarantined): open deals whose close date already passed
    open_idx = opp_raw.index[opp_raw.stage.isin(C.OPEN_STAGES)
                             & ~opp_raw.opp_id.isin(orphans.opp_id)
                             & ~opp_raw.index.isin(bad_amt)
                             & (pd.to_datetime(opp_raw.created_date) <= pd.Timestamp(add_days(C.AS_OF, -60)))]
    stale = rng.choice(open_idx, 23, replace=False)
    opp_raw.loc[stale, "close_date"] = [add_days(C.AS_OF, -int(rng.integers(3, 40))) for _ in stale]
    injected["past_due_close_dates"] = opp_raw.loc[stale, "opp_id"].tolist()
    return acc_raw, opp_raw, injected


# ---------------------------------------------------------------------------
def main():
    acc = build_accounts()
    terr, spec = build_territories(acc)
    opps = simulate(acc)
    simulate_browser(acc, opps)

    opp = pd.DataFrame(opps)
    opp = opp[opp.close_date >= C.WINDOW_START].copy()           # keep FY24 Q1 onward
    opp = opp.sort_values(["created_date", "account_idx"]).reset_index(drop=True)
    opp.insert(0, "opp_id", [f"O{100000 + k}" for k in range(len(opp))])
    opp.insert(1, "account_id", acc.account_id.to_numpy()[opp.account_idx.to_numpy()])
    opp["specialist_covered"] = acc.specialist_covered.to_numpy()[opp.account_idx.to_numpy()]
    # POV start = entry into Technical Validation (only for deals that got that far)
    reached_tv = (opp.stage.isin(["Technical Validation", "Proposal", "Negotiation", "Closed Won"])
                  | opp.loss_stage.isin(["Technical Validation", "Proposal", "Negotiation"]))
    pov = [add_days(c, cy * STAGE_CUTS[1]) for c, cy in zip(opp.created_date, opp.cycle_days)]
    opp["pov_start_date"] = [p if (r and p <= C.AS_OF) else None for p, r in zip(pov, reached_tv)]
    opp = opp.drop(columns=["account_idx", "fate_won", "cycle_days"])
    opp["amount"] = opp.amount.round(-2)

    acc_out = acc.drop(columns=["mobile_users"])
    acc_raw, opp_raw, injected = inject_quality_issues(acc_out, opp)

    C.DATA_RAW.mkdir(parents=True, exist_ok=True)
    acc_raw.to_csv(C.DATA_RAW / "accounts.csv", index=False)
    opp_raw.to_csv(C.DATA_RAW / "opportunities.csv", index=False)
    terr.to_csv(C.DATA_RAW / "territories.csv", index=False)
    spec.to_csv(C.DATA_RAW / "specialists.csv", index=False)
    enablement_series().to_csv(C.DATA_RAW / "launch_enablement_weekly.csv", index=False)
    (C.DATA_RAW / "_injected_issues.json").write_text(json.dumps(injected, indent=2))

    # Calibration summary
    print(f"accounts={len(acc)}  opportunities={len(opp)}  territories={len(terr)}  specialists={len(spec)}")
    print(f"attach rate={acc.has_prisma_access.mean():.3f}  SASE ARR=${acc.sase_arr.sum()/1e6:.1f}M  "
          f"browser adopters={acc.has_prisma_browser.sum()} (early {acc.browser_early_adopter.sum()})")
    won = opp[opp.stage == "Closed Won"].copy()
    won["fq"] = [C.fq_label(d) for d in won.close_date]
    print(won[won.opp_type != "Browser"].groupby("fq").amount.agg(["count", "sum"]).assign(sum=lambda d: (d["sum"] / 1e6).round(2)))


if __name__ == "__main__":
    main()
