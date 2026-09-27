"""
Central configuration for the SASE GTM Operating System.

Every assumption that shapes the synthetic data or the analysis lives here,
so a reviewer can see (and challenge) each one in a single place.
All data produced from these settings is SYNTHETIC.
"""
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_CLEAN = ROOT / "data" / "clean"
DATA_PROCESSED = ROOT / "data" / "processed"
DOCS = ROOT / "docs"
APP = ROOT / "app"

SEED = 2027

# ---------------------------------------------------------------------------
# Calendar. Palo Alto Networks' fiscal year runs Aug 1 - Jul 31 (FY27 began
# Aug 1, 2026). The dataset is frozen at the as-of date below.
# ---------------------------------------------------------------------------
AS_OF = date(2026, 9, 25)          # FY27 Q1, week 8
EPOCH = date(2023, 1, 1)           # day-index origin used in the web app
SIM_START = date(2023, 2, 1)       # simulation warm-up (FY23 Q3)
WINDOW_START = date(2023, 8, 1)    # first quarter kept in the dataset: FY24 Q1
BROWSER_RELAUNCH = date(2026, 3, 23)  # Prisma Browser agentic-AI evolution (public announcement)
FY_START_MONTH = 8


def fiscal_year(d: date) -> int:
    return d.year + 1 if d.month >= FY_START_MONTH else d.year


def fiscal_quarter(d: date) -> int:
    return ((d.month - FY_START_MONTH) % 12) // 3 + 1


def fq_label(d: date) -> str:
    return f"FY{fiscal_year(d) % 100:02d} Q{fiscal_quarter(d)}"


def quarter_bounds(fy: int, q: int):
    """Start and end dates of a fiscal quarter."""
    start_month = (FY_START_MONTH - 1 + 3 * (q - 1)) % 12 + 1
    start_year = fy - 1 if start_month >= FY_START_MONTH else fy
    start = date(start_year, start_month, 1)
    end_month = start_month + 3
    end_year = start_year
    if end_month > 12:
        end_month -= 12
        end_year += 1
    end = date.fromordinal(date(end_year, end_month, 1).toordinal() - 1)
    return start, end


# ---------------------------------------------------------------------------
# Book of business
# ---------------------------------------------------------------------------
N_ACCOUNTS = 4200

SEGMENTS = ["Large Enterprise", "Enterprise", "Mid-Market", "Commercial"]
SEGMENT_MIX = [0.07, 0.18, 0.35, 0.40]

REGIONS = ["AMER", "EMEA", "JAPAC"]
REGION_MIX = [0.50, 0.30, 0.20]
COUNTRIES = {
    "AMER": (["United States", "Canada", "Brazil", "Mexico"], [0.78, 0.10, 0.07, 0.05]),
    "EMEA": (["United Kingdom", "Germany", "France", "Netherlands", "UAE", "Italy", "Spain"],
             [0.26, 0.22, 0.16, 0.10, 0.08, 0.10, 0.08]),
    "JAPAC": (["Japan", "Australia", "India", "Singapore", "South Korea"],
              [0.34, 0.24, 0.20, 0.12, 0.10]),
}

INDUSTRIES = [
    "Financial Services", "Healthcare", "Manufacturing", "Retail", "Technology",
    "Public Sector", "Energy & Utilities", "Professional Services", "Education",
    "Telecommunications",
]
INDUSTRY_MIX = [0.16, 0.12, 0.14, 0.10, 0.12, 0.08, 0.06, 0.09, 0.06, 0.07]

# Incumbent for remote access / SSE before any Prisma Access purchase.
INCUMBENTS = ["GlobalProtect VPN", "Third-party VPN", "Zscaler", "Netskope",
              "Cisco", "Cloudflare", "Fortinet"]
SSE_COMPETITORS = ["Zscaler", "Netskope", "Cisco", "Cloudflare", "Fortinet"]
COMPETITORS = ["Zscaler", "Netskope", "Cisco", "Fortinet", "Cloudflare", "No competitor"]

# ---------------------------------------------------------------------------
# Pricing assumptions used to size whitespace (illustrative list-price style
# figures, not Palo Alto Networks pricing).
# ---------------------------------------------------------------------------
PRICE_PER_USER = {"Large Enterprise": 75, "Enterprise": 95, "Mid-Market": 110, "Commercial": 125}
PRICE_PER_BRANCH = 3600          # SD-WAN / remote-network site, annual
LAND_SHARE = {"Large Enterprise": 0.30, "Enterprise": 0.40, "Mid-Market": 0.55, "Commercial": 0.70}
BROWSER_PRICE_PER_USER = 48

# ---------------------------------------------------------------------------
# Coverage design: share of core territories with a SASE specialist overlay.
# This is the lever the analysis is designed to test.
# ---------------------------------------------------------------------------
ACCOUNTS_PER_CORE_TERRITORY = {"Large Enterprise": 12, "Enterprise": 36, "Mid-Market": 90, "Commercial": 170}
SPECIALIST_COVERAGE = {
    ("AMER", "Large Enterprise"): 1.00, ("AMER", "Enterprise"): 1.00,
    ("AMER", "Mid-Market"): 1.00, ("AMER", "Commercial"): 0.60,
    ("EMEA", "Large Enterprise"): 1.00, ("EMEA", "Enterprise"): 0.80,
    ("EMEA", "Mid-Market"): 0.25, ("EMEA", "Commercial"): 0.00,
    ("JAPAC", "Large Enterprise"): 1.00, ("JAPAC", "Enterprise"): 0.50,
    ("JAPAC", "Mid-Market"): 0.00, ("JAPAC", "Commercial"): 0.00,
}
ACCOUNTS_PER_SPECIALIST = {"Large Enterprise": 45, "Enterprise": 80, "Mid-Market": 180, "Commercial": 340}

# ---------------------------------------------------------------------------
# Sales process
# ---------------------------------------------------------------------------
STAGES = ["Discover", "Qualify", "Technical Validation", "Proposal", "Negotiation",
          "Closed Won", "Closed Lost"]
OPEN_STAGES = STAGES[:5]
STAGE_PROBABILITY = {"Discover": 0.10, "Qualify": 0.20, "Technical Validation": 0.40,
                     "Proposal": 0.60, "Negotiation": 0.80, "Closed Won": 1.0, "Closed Lost": 0.0}
STAGE_SLA_DAYS = {"Discover": 30, "Qualify": 30, "Technical Validation": 45,
                  "Proposal": 30, "Negotiation": 30}
SOURCES = ["AE-sourced", "Specialist-sourced", "Partner-sourced", "Marketing-sourced"]
LOSS_REASONS = ["Chose competitor", "No decision", "Price", "POV outcome",
                "Timing or budget", "Incumbent contract term"]
PRODUCTS = ["Prisma Access", "Prisma SASE bundle", "SD-WAN add-on", "Seat expansion", "Prisma Browser"]
OPP_TYPES = ["Land", "Expansion", "Browser"]

# FY27 planning defaults
FY27_GROWTH_TARGET = 0.35
QUARTER_SEASONALITY = [0.21, 0.26, 0.23, 0.30]   # FY Q1..Q4 share of annual bookings
SPECIALIST_COST = 300_000                       # fully loaded annual cost, illustrative

PLAYS = [
    "Competitive displacement",
    "Renewal-timed attach",
    "GlobalProtect migration",
    "Branch transformation",
    "Partner-led nurture",
]

# Author shown in the app and docs. Fill in links before publishing; empty links are hidden.
AUTHOR = "Jash Shah"
AUTHOR_LINKS = {"LinkedIn": "", "GitHub": "https://github.com/jashshah127/sase-gtm-os", "Resume": ""}
