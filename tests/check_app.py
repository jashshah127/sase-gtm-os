"""
End-to-end check of the built web app in a real (headless) browser.

1. Every route renders with no JavaScript errors.
2. The app's live numbers match the Python pipeline (data/processed/*.json).
3. Filters, sliders, tabs, and the weekly review respond.
4. Screenshots for the README (desktop and mobile).

Run:  python tests/check_app.py   (requires: pip install playwright && playwright install chromium)
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "data/processed/summary.json").read_text())
P = json.loads((ROOT / "data/processed/planning.json").read_text())
SHOTS = ROOT / "docs/screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)
failures = []


def check(name, got, want, tol):
    ok = abs(got - want) <= tol * max(1.0, abs(want))
    print(f"  {'ok  ' if ok else 'FAIL'} {name:<34} app={got:,.6g}  pipeline={want:,.6g}")
    if not ok:
        failures.append(name)


def main(full_shots_dir=None):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        page.on("console", lambda m: errors.append(f"console: {m.text}")
                if m.type == "error" and "Failed to load resource" not in m.text else None)
        page.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        page.route("**/fonts.gstatic.com/**", lambda r: r.abort())
        url = (ROOT / "index.html").as_uri()

        def go(hash_, shot=None, settle=350):
            page.goto(f"{url}#{hash_}")
            page.wait_for_timeout(settle)
            if shot:
                page.screenshot(path=str(SHOTS / f"{shot}.png"))
                if full_shots_dir:
                    page.screenshot(path=str(Path(full_shots_dir) / f"{shot}_full.png"), full_page=True)

        print("routes")
        go("briefing", "01_briefing")
        go("market", "07_market")
        assert "Palo Alto" in page.inner_text(".claim h1"), "market claim missing"
        assert page.locator("[data-market-panel]").count() == 3, "expected three public-data panels"
        assert page.locator("#mk-growth svg").count() == 1 and page.locator("#mk-arr svg").count() == 1
        print("  ok   market context renders (claim, growth, ARR timeline, three data panels)")
        go("revenue", "02_revenue")
        val = lambda k: page.get_attribute(f'[data-kpi="{k}"]', "data-value")

        print("revenue KPIs vs pipeline/metrics.py")
        check("attach rate", float(val("attach")), S["attach_rate"], 1e-3)
        check("SASE ARR", float(val("arr")), S["sase_arr"] + S["browser_arr"], 1e-9)
        check("Q1 bookings to date", float(val("qtd")), S["q1_qtd_bookings"], 1e-9)
        check("Q2 pipeline coverage", float(val("q2cov")), S["pipeline_coverage"][1]["coverage"], 5e-3)
        check("FY26 land win rate", float(val("winrate")), S["fy26_land_win_rate"], 1e-3)
        check("median sales cycle", float(val("cycle")), S["median_cycle_days_fy26_won_land"], 1e-9)
        claim = page.inner_text("#rev-claim")
        check("whitespace total in claim", float(claim.split("remaining $")[1].split("M")[0]),
              round(S["whitespace"]["expected_value_total"] / 1e6, 1), 1e-9)

        for tab in ["whitespace", "winloss", "trends", "pipeline"]:
            page.click(f'[data-tab="{tab}"]')
            page.wait_for_timeout(200)
            if full_shots_dir:
                page.screenshot(path=str(Path(full_shots_dir) / f"revenue_{tab}_full.png"), full_page=True)

        page.select_option("#f-rg", "1")
        page.wait_for_timeout(200)
        emea = page.inner_text("#rev-claim")
        assert emea.startswith("EMEA:"), f"filter did not apply: {emea}"
        print(f"  ok   region filter: {emea[:70]}...")
        page.select_option("#f-rg", "-1")

        print("planning engine vs pipeline/planning.py")
        go("planning", "03_planning")
        check("baseline attainment", float(val("plan-att")), P["baseline"]["attainment"], 1e-6)
        for i, sc in enumerate(P["scenarios"]):
            got = float(page.get_attribute(f'[data-scn="{i}"]', "data-att"))
            check(f"scenario: {sc['name'][:26]}", got, sc["attainment"], 1e-4)
        page.click("#plan-rec")
        page.wait_for_timeout(250)
        rec_att = float(val("plan-att"))
        assert rec_att >= 1.0, f"recommended plan should reach target, got {rec_att}"
        print(f"  ok   recommended plan reaches {rec_att:.1%}")
        page.fill("#ctl-lead", "6")
        page.dispatch_event("#ctl-lead", "input")
        page.wait_for_timeout(250)
        print(f"  ok   lead time 6 months -> {float(val('plan-att')):.1%}")
        if full_shots_dir:
            page.screenshot(path=str(Path(full_shots_dir) / "planning_full.png"), full_page=True)

        print("other modules")
        go("launch", "04_launch")
        assert page.locator("#ln-targets tbody tr").count() == 20
        go("exec", "05_exec")
        text = page.get_attribute("#wbr", "data-text")
        assert text and text.startswith("Subject: SASE WBR"), "weekly review did not render"
        print(f"  ok   WBR: {text.splitlines()[0][:90]}...")
        page.select_option("#wbr-week", index=0)
        page.wait_for_timeout(200)
        go("cadence", "06_cadence")
        page.fill("#md-q", "coverage")
        page.wait_for_timeout(150)
        n = page.locator("#md-table tbody tr").count()
        assert n >= 2, f"search returned {n} rows"
        print(f"  ok   metric search 'coverage' -> {n} rows")
        if full_shots_dir:
            for r in ["briefing", "market", "launch", "exec", "cadence"]:
                go(r)
                page.screenshot(path=str(Path(full_shots_dir) / f"{r}_full.png"), full_page=True)

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        mobile.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        mobile.route("**/fonts.gstatic.com/**", lambda r: r.abort())
        mobile.on("pageerror", lambda e: errors.append(f"mobile pageerror: {e}"))
        for r in ["briefing", "planning"]:
            mobile.goto(f"{url}#{r}")
            mobile.wait_for_timeout(300)
            mobile.screenshot(path=str(SHOTS / f"mobile_{r}.png"))
        browser.close()

    if errors:
        print("JavaScript errors:")
        for e in errors:
            print("  ", e)
        failures.append("javascript errors")
    print("RESULT:", "all checks passed" if not failures else f"FAILED {failures}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
