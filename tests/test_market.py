"""
Offline tests for pipeline/market.py. Uses FAKE fixtures in tests/fixtures_market/.
Run with pytest, or directly:  python tests/test_market.py
"""
import math
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
import market  # noqa: E402

FIX = ROOT / "tests" / "fixtures_market"


def test_parse_band():
    assert market.parse_band("Total") is None
    assert market.parse_band("<20") == (0, 20)
    assert market.parse_band("02: <5 employees") == (0, 5)
    assert market.parse_band("500-749") == (500, 750)
    assert market.parse_band("1,000-1,499") == (1000, 1500)
    assert market.parse_band("20,000+") == (20000, math.inf)
    assert market.parse_band("10,000 or more") == (10000, math.inf)
    assert market.parse_band("unknown") is None


def test_curated_loads_and_public_missing():
    out = market.build(public_dir=Path("/nonexistent"))
    cu = out["curated"]
    assert cu["status"] == "loaded" and len(cu["rows"]) >= 10
    tickers = {g["ticker"] for g in cu["growth"] if g["kind"] == "company"}
    assert {"PANW", "ZS", "FTNT", "NTSK"} <= tickers
    assert any(g["kind"] == "market" for g in cu["growth"])
    assert all(v["status"] == "missing" for v in out["public"].values())


def test_public_fixtures():
    out = market.build(public_dir=FIX)
    sec, kev, census = (out["public"][k] for k in ("sec", "kev", "census"))
    assert sec["status"] == kev["status"] == census["status"] == "loaded", out["public"]
    a = next(r for r in sec["data"] if r["ticker"] == "TSTA")
    assert a["revenue"] == 1500                                  # quarterly 10-Q row ignored
    assert abs(a["revenue_yoy"] - 0.25) < 1e-9                   # 1500 vs restated 1200 (latest filing wins)
    assert abs(a["revenue_cagr3"] - ((1500 / 800) ** (1 / 3) - 1)) < 1e-3
    assert abs(a["rpo_yoy"] - 0.30) < 1e-9
    b = next(r for r in sec["data"] if r["ticker"] == "TSTB")
    assert b["revenue"] == 500 and abs(b["revenue_yoy"] - 0.25) < 1e-9   # 8-K row ignored
    assert kev["data"]["total"] == 6 and kev["data"]["ransomware_total"] == 3
    assert kev["data"]["totals"]["Vendor One"] == 3
    seg = {s["segment"]: s for s in census["data"]["segments"]}
    assert census["data"]["year"] == 2022                         # latest year only
    assert seg["Commercial"]["firms"] == 500
    assert seg["Mid-Market"]["firms"] == 100 + 60 + 50 + 30          # '500+' aggregate not double counted
    assert seg["Enterprise"]["firms"] == 20 + 20 + 10
    assert seg["Large Enterprise"]["firms"] == 6 + 4
    assert census["data"]["below_100"]["firms"] == 8000 + 1200
    assert census["data"]["sectors"][0]["naics"] == "52"
    assert sec["fetched_at"] == "2026-09-27T12:00:00Z"


def test_invalid_schema_is_reported_not_raised():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "kev_edge_vendors.csv").write_text("cve_id,vendor\nX,Y\n")
        out = market.build(public_dir=Path(d))
        status = out["public"]["kev"]["status"]
        assert status.startswith("invalid: missing columns"), status
        assert out["public"]["sec"]["status"] == "missing"


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"{len(tests)} tests passed")
