"""
Market context from REAL public data: the one module that is not synthetic.

Two kinds of input, deliberately kept apart:
  data/curated/  Hand-curated figures from earnings releases and analyst press
                 releases. Every row carries its source URL. Verify before quoting.
  data/public/   Machine-fetched datasets written by pipeline/fetch_public_data.py
                 (SEC EDGAR, CISA KEV, Census SUSB). Optional: each panel in the app
                 shows as pending until its file exists and passes the schema check.

Writes data/processed/market.json
Run:   python pipeline/market.py [--public-dir PATH] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import pandas as pd

import config as C

CURATED_DIR = C.ROOT / "data" / "curated"
PUBLIC_DIR = C.ROOT / "data" / "public"

SCHEMAS = {
    "competitor_kpis": ["company", "ticker", "metric", "metric_scope", "period_end", "fiscal_period", "value_usd_m",
                        "yoy_growth_pct", "primary", "chart_series", "source_title", "source_url", "published", "notes"],
    "market_context": ["source", "metric", "period", "period_end", "value", "unit", "precision", "yoy_growth_pct",
                       "source_url", "published", "notes"],
    "sec_financials": ["ticker", "cik", "concept", "fiscal_year", "fiscal_period", "form", "period_start",
                       "period_end", "value_usd", "filed"],
    "kev_edge_vendors": ["cve_id", "vendor", "product", "vulnerability_name", "date_added", "known_ransomware_use"],
    "census_susb": ["year", "naics", "naics_label", "size_band", "firms", "establishments", "employment"],
}
PUBLIC_FILES = {"sec": ("sec_financials.csv", "sec_financials"),
                "kev": ("kev_edge_vendors.csv", "kev_edge_vendors"),
                "census": ("census_susb.csv", "census_susb")}
PUBLIC_SOURCES = [
    ("SEC EDGAR APIs (company facts)", "https://www.sec.gov/search-filings/edgar-application-programming-interfaces"),
    ("CISA Known Exploited Vulnerabilities catalog", "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"),
    ("US Census Bureau, Statistics of U.S. Businesses", "https://www.census.gov/programs-surveys/susb/about.html"),
]
TICKER_NAMES = {"PANW": "Palo Alto Networks", "ZS": "Zscaler", "FTNT": "Fortinet", "NTSK": "Netskope",
                "NET": "Cloudflare", "CSCO": "Cisco", "CHKP": "Check Point", "CRWD": "CrowdStrike"}
REV_CONCEPTS = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"]
RPO_CONCEPT = "RevenueRemainingPerformanceObligation"
SEGMENT_BOUNDS = [("Commercial", 100, 500), ("Mid-Market", 500, 2000),
                  ("Enterprise", 2000, 10000), ("Large Enterprise", 10000, math.inf)]
TOTAL_CODES = {"--", "00", "0", "total", "all", ""}
NAICS_TO_INDUSTRY = {"52": "Financial Services", "62": "Healthcare", "31-33": "Manufacturing", "44-45": "Retail",
                     "51": "Technology and Telecommunications", "54": "Professional Services",
                     "61": "Education", "22": "Energy & Utilities", "21": "Energy & Utilities"}


# ---------------------------------------------------------------------------
def clean(obj):
    """Make an object JSON-safe: NaN and infinity become None, numpy types become Python types."""
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        obj = obj.item()
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def day_index(value):
    d = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(d) else int((d - pd.Timestamp(C.EPOCH)).days)


def load_csv(path: Path, schema: str):
    """Return (DataFrame, status). Status is 'loaded', 'missing', or 'invalid: <reason>'."""
    if not path.exists():
        return None, "missing"
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception as exc:  # noqa: BLE001 - any read failure is reported, not raised
        return None, f"invalid: could not read the file ({exc})"
    missing = [c for c in SCHEMAS[schema] if c not in df.columns]
    if missing:
        return None, f"invalid: missing columns {', '.join(missing)}"
    if df.empty:
        return None, "invalid: the file has no rows"
    return df, "loaded"


def num(series):
    return pd.to_numeric(series.astype(str).str.replace(",", "").str.strip(), errors="coerce")


# ---------------------------------------------------------------------------
# Curated figures
# ---------------------------------------------------------------------------
def curated(curated_dir: Path) -> dict:
    kpi, s1 = load_csv(curated_dir / "competitor_kpis.csv", "competitor_kpis")
    ctx, s2 = load_csv(curated_dir / "market_context.csv", "market_context")
    if kpi is None or ctx is None:
        raise SystemExit(f"Curated data problem: competitor_kpis.csv is {s1}; market_context.csv is {s2}")
    kpi = kpi.assign(value=num(kpi.value_usd_m), growth=num(kpi.yoy_growth_pct) / 100,
                     t=kpi.period_end.map(day_index), is_primary=kpi.primary.str.strip() == "1")
    bad = kpi[kpi.value.isna() | kpi.t.isna()]
    if len(bad):
        raise SystemExit(f"Curated competitor rows with a bad value or date (CSV rows {[i + 2 for i in bad.index]})")
    ctx = ctx.assign(v=num(ctx.value), growth=num(ctx.yoy_growth_pct) / 100, t=ctx.period_end.map(day_index))

    rows = [{"company": r.company, "ticker": r.ticker, "metric": r.metric, "scope": r.metric_scope,
             "period_end": r.period_end, "fiscal_period": r.fiscal_period, "value": r.value, "growth": r.growth,
             "source_title": r.source_title, "source_url": r.source_url, "notes": r.notes}
            for r in kpi.itertuples()]
    latest = (kpi.sort_values("t").groupby(["company", "metric"], sort=False).tail(1)
              .sort_values(["company", "t"]))
    scoreboard = [{"company": r.company, "metric": r.metric, "scope": r.metric_scope, "fiscal_period": r.fiscal_period,
                   "period_end": r.period_end, "value": r.value, "growth": r.growth, "source_title": r.source_title,
                   "source_url": r.source_url, "notes": r.notes} for r in latest.itertuples()]
    series = {}
    for name, g in kpi[kpi.chart_series.str.strip() != ""].groupby("chart_series"):
        g = g.sort_values("t")
        series[name] = [{"t": int(r.t), "v": r.value / 1000, "label": f"{r.fiscal_period} ({r.period_end})"}
                        for r in g.itertuples()]

    growth = [{"kind": "company", "company": r.company, "ticker": r.ticker, "metric": r.metric,
               "fiscal_period": r.fiscal_period, "period_end": r.period_end, "growth": r.growth}
              for r in kpi[kpi.is_primary & kpi.growth.notna()].itertuples()]
    quarterly = ctx[ctx.metric == "SASE market revenue"].sort_values("t")
    if len(quarterly):
        q = quarterly.iloc[-1]
        growth.append({"kind": "market", "company": "SASE market (Dell'Oro)", "ticker": "", "metric": "manufacturer revenue",
                       "fiscal_period": q.period, "period_end": q.period_end, "growth": q.growth})
    market = {
        "quarterly": [{"period": r.period, "value": r.v, "unit": r.unit, "precision": r.precision, "growth": r.growth,
                       "source_url": r.source_url, "notes": r.notes} for r in quarterly.itertuples()],
        "facts": [{"metric": r.metric, "period": r.period, "value": r.v, "unit": r.unit, "precision": r.precision,
                   "notes": r.notes, "source_url": r.source_url}
                  for r in ctx[ctx.metric != "SASE market revenue"].itertuples()],
    }
    seen, sources = set(), []
    for title, url in list(zip(kpi.source_title, kpi.source_url)) + [(f"{s}: {m} ({p})", u) for s, m, p, u in
                                                                       zip(ctx.source, ctx.metric, ctx.period, ctx.source_url)]:
        if url not in seen:
            seen.add(url)
            sources.append({"title": title, "url": url})
    return {"status": "loaded", "rows": rows, "scoreboard": scoreboard, "series": series,
            "growth": growth, "market": market, "sources": sources}


# ---------------------------------------------------------------------------
# Machine-fetched datasets
# ---------------------------------------------------------------------------
def sec_summary(df: pd.DataFrame) -> list:
    df = df.assign(value=num(df.value_usd), period_start=pd.to_datetime(df.period_start, errors="coerce"),
                   period_end=pd.to_datetime(df.period_end, errors="coerce"),
                   filed=pd.to_datetime(df.filed, errors="coerce"), form=df.form.str.upper().str.strip())
    df = df[df.form.isin(["10-K", "10-Q", "10-K/A", "10-Q/A"]) & df.value.notna() & df.period_end.notna()]
    out = []
    for ticker, g in df.groupby("ticker"):
        rev = g[g.concept.isin(REV_CONCEPTS) & g.period_start.notna()].copy()
        rev["days"] = (rev.period_end - rev.period_start).dt.days
        ann = rev[rev.days.between(350, 380)].copy()            # full fiscal years only
        ann["pref"] = ann.concept.map({c: i for i, c in enumerate(REV_CONCEPTS)})
        ann = (ann.sort_values(["period_end", "pref", "filed"], ascending=[True, True, False])
               .drop_duplicates("period_end"))                  # latest filing wins for each period
        rec = {"ticker": ticker, "company": TICKER_NAMES.get(ticker, ticker), "latest_fy_end": None, "revenue": None,
               "revenue_yoy": None, "revenue_cagr3": None, "rpo": None, "rpo_date": None, "rpo_yoy": None,
               "series": [{"period_end": d.strftime("%Y-%m-%d"), "value": float(v)}
                          for d, v in zip(ann.period_end, ann.value)][-5:]}
        if len(ann):
            last = ann.iloc[-1]
            rec.update(latest_fy_end=last.period_end.strftime("%Y-%m-%d"), revenue=float(last.value))
            if len(ann) >= 2:
                prev = ann.iloc[-2]
                if 330 <= (last.period_end - prev.period_end).days <= 400 and prev.value > 0:
                    rec["revenue_yoy"] = float(last.value / prev.value - 1)
            if len(ann) >= 4:
                base = ann.iloc[-4]
                years = (last.period_end - base.period_end).days / 365.25
                if 2.7 <= years <= 3.3 and base.value > 0:
                    rec["revenue_cagr3"] = float((last.value / base.value) ** (1 / years) - 1)
        rpo = (g[g.concept == RPO_CONCEPT].sort_values(["period_end", "filed"], ascending=[True, False])
               .drop_duplicates("period_end"))
        if len(rpo):
            r = rpo.iloc[-1]
            rec.update(rpo=float(r.value), rpo_date=r.period_end.strftime("%Y-%m-%d"))
            prior = rpo[rpo.period_end.between(r.period_end - pd.Timedelta(days=385), r.period_end - pd.Timedelta(days=345))]
            if len(prior) and prior.iloc[-1].value > 0:
                rec["rpo_yoy"] = float(r.value / prior.iloc[-1].value - 1)
        out.append(rec)
    return sorted(out, key=lambda r: -(r["revenue"] or 0))


def kev_summary(df: pd.DataFrame) -> dict:
    df = df.assign(date=pd.to_datetime(df.date_added, errors="coerce"))
    df = df[df.date.notna()].copy()
    if df.empty:
        raise ValueError("no parseable date_added values")
    df["year"] = df.date.dt.year
    last_year = int(df.year.max())
    years = list(range(max(int(df.year.min()), last_year - 5), last_year + 1))
    totals = df.vendor.value_counts()
    top = totals.index[:6].tolist()
    matrix = {v: [int(((df.vendor == v) & (df.year == y)).sum()) for y in years] for v in top}
    other = [int(((~df.vendor.isin(top)) & (df.year == y)).sum()) for y in years]
    if any(other):
        matrix["Other edge vendors"] = other
    ransom = df[df.known_ransomware_use.str.strip().str.lower().isin(["known", "yes", "true", "1"])]
    recent = df.sort_values("date", ascending=False).head(8)
    return {"years": years, "last_year_partial": last_year == pd.Timestamp(C.AS_OF).year, "matrix": matrix,
            "totals": {k: int(v) for k, v in totals.items()}, "total": int(len(df)),
            "first_year": int(df.year.min()), "ransomware_total": int(len(ransom)),
            "ransomware": {k: int(v) for k, v in ransom.vendor.value_counts().items()},
            "recent": [{"date": d.strftime("%Y-%m-%d"), "cve_id": c, "vendor": v, "product": p, "name": n,
                        "ransomware": str(k).strip()}
                       for d, c, v, p, n, k in zip(recent["date"], recent["cve_id"], recent["vendor"], recent["product"],
                                                   recent.vulnerability_name, recent.known_ransomware_use)]}


def parse_band(label):
    """Turn an employment size-band label into (low, high_exclusive), or None for totals and unknowns."""
    t = re.sub(r"^\s*\d+\s*:\s*", "", str(label)).lower().replace(",", "").strip()
    if not t or "total" in t:
        return None
    m = re.search(r"(\d+)\s*(?:-|to|–|—)\s*(\d+)", t)
    if m:
        return int(m.group(1)), int(m.group(2)) + 1
    m = re.search(r"(\d+)\s*(?:\+|or more|and over|or greater)", t)
    if m:
        return int(m.group(1)), math.inf
    m = re.search(r"(?:<|less than|under|fewer than)\s*(\d+)", t)
    if m:
        return 0, int(m.group(1))
    return None


def atomic_bands(bands: list) -> list:
    """Drop aggregate bands (like '500+') whenever finer bands inside them exist, to avoid double counting."""
    uniq = {}
    for label, lo, hi, firms, emp in bands:
        uniq.setdefault((lo, hi), (label, lo, hi, firms, emp))
    items = list(uniq.values())
    return [b for b in items
            if not any(o is not b and o[1] >= b[1] and o[2] <= b[2] and (o[1], o[2]) != (b[1], b[2]) for o in items)]


def segment_counts(g: pd.DataFrame):
    bands = [(r.size_band, *r.band, r.firms, r.employment) for r in g.itertuples() if r.band]
    res = {s: {"firms": 0.0, "employment": 0.0} for s, _, _ in SEGMENT_BOUNDS}
    below, unmapped = {"firms": 0.0, "employment": 0.0}, []
    for label, lo, hi, firms, emp in atomic_bands(bands):
        firms, emp = (0.0 if pd.isna(firms) else firms), (0.0 if pd.isna(emp) else emp)
        if hi <= 100:
            below["firms"] += firms
            below["employment"] += emp
            continue
        seg = next((s for s, slo, shi in SEGMENT_BOUNDS if lo >= slo and hi <= shi), None)
        if seg:
            res[seg]["firms"] += firms
            res[seg]["employment"] += emp
        else:
            unmapped.append(str(label))
    return res, below, unmapped


def census_summary(df: pd.DataFrame, synthetic_mix: dict) -> dict:
    df = df.assign(firms=num(df.firms), establishments=num(df.establishments), employment=num(df.employment),
                   year_n=num(df.year), band=df.size_band.map(parse_band))
    year = int(df.year_n.max())
    df = df[df.year_n == year]
    code = df.naics.str.strip().str.lower()
    is_total = code.isin(TOTAL_CODES) | df.naics_label.str.lower().str.contains("total")
    if is_total.any():
        base, basis = df[is_total], "all-industry total rows"
    else:
        base = (df.groupby("size_band", as_index=False)[["firms", "employment"]].sum()
                .assign(band=lambda d: d.size_band.map(parse_band)))
        basis = "sum of sector rows (a firm active in several sectors is counted once per sector)"
    res, below, unmapped = segment_counts(base)
    total_firms = sum(v["firms"] for v in res.values())
    total_emp = sum(v["employment"] for v in res.values())
    if total_firms == 0:
        raise ValueError("no size bands of 100+ employees could be mapped to segments")
    segments = [{"segment": s, "firms": res[s]["firms"], "employment": res[s]["employment"],
                 "share_firms": res[s]["firms"] / total_firms,
                 "share_employment": res[s]["employment"] / total_emp if total_emp else None,
                 "synthetic_share": synthetic_mix.get(s)} for s, _, _ in SEGMENT_BOUNDS]
    sectors = []
    for (naics, label), g in df[~is_total].groupby(["naics", "naics_label"]):
        r, _, _ = segment_counts(g)
        sectors.append({"naics": naics, "label": label, "industry": NAICS_TO_INDUSTRY.get(str(naics).strip(), ""),
                        "firms_500_plus": r["Mid-Market"]["firms"] + r["Enterprise"]["firms"] + r["Large Enterprise"]["firms"],
                        "firms_2000_plus": r["Enterprise"]["firms"] + r["Large Enterprise"]["firms"]})
    sectors = sorted(sectors, key=lambda s: -s["firms_2000_plus"])[:10]
    return {"year": year, "basis": basis, "segments": segments, "below_100": below,
            "unmapped_bands": sorted(set(unmapped)), "sectors": sectors}


def synthetic_segment_mix() -> dict:
    path = C.DATA_PROCESSED / "accounts_scored.csv"
    if not path.exists():
        return {}
    seg = pd.read_csv(path, usecols=["segment"]).segment
    return {k: float(v) for k, v in seg.value_counts(normalize=True).items()}


def public(public_dir: Path) -> dict:
    manifest = {}
    if (public_dir / "manifest.json").exists():
        try:
            manifest = json.loads((public_dir / "manifest.json").read_text())
        except json.JSONDecodeError:
            manifest = {"error": "manifest.json is not valid JSON"}
    builders = {"sec": sec_summary, "kev": kev_summary,
                "census": lambda d: census_summary(d, synthetic_segment_mix())}
    out = {}
    for key, (filename, schema) in PUBLIC_FILES.items():
        df, status = load_csv(public_dir / filename, schema)
        entry = {"status": status, "file": f"data/public/{filename}", "data": None,
                 "fetched_at": (manifest.get(filename) or {}).get("fetched_at") if isinstance(manifest, dict) else None}
        if df is not None:
            try:
                entry["data"] = builders[key](df)
                entry["rows"] = int(len(df))
            except Exception as exc:  # noqa: BLE001 - surface the problem in the app instead of crashing
                entry.update(status=f"invalid: {exc}", data=None)
        out[key] = entry
    return out


def build(public_dir: Path = PUBLIC_DIR, curated_dir: Path = CURATED_DIR) -> dict:
    return clean({"as_of": str(C.AS_OF), "curated": curated(curated_dir), "public": public(public_dir),
                  "public_sources": [{"title": t, "url": u} for t, u in PUBLIC_SOURCES]})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--public-dir", type=Path, default=PUBLIC_DIR)
    ap.add_argument("--curated-dir", type=Path, default=CURATED_DIR)
    ap.add_argument("--out", type=Path, default=C.DATA_PROCESSED / "market.json")
    args = ap.parse_args(argv)
    result = build(args.public_dir, args.curated_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=1, allow_nan=False))
    cu = result["curated"]
    print(f"curated: {len(cu['rows'])} competitor rows, {len(cu['market']['quarterly'])} market quarters, "
          f"{len(cu['sources'])} sources")
    for key, entry in result["public"].items():
        extra = f" ({entry.get('rows')} rows)" if entry.get("rows") else ""
        print(f"public {key:<7} {entry['status']}{extra}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
