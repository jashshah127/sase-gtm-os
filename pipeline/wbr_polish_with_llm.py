"""
Optional: tighten a weekly business review draft with Claude.

The app's Executive layer drafts the WBR with deterministic rules, so every number
is traceable. This script is an optional last-mile editor that must not change numbers.

    1. In the app, open Executive layer and select Copy as text; save it as wbr.txt
    2. export ANTHROPIC_API_KEY=...    (optional: export ANTHROPIC_MODEL=...)
    3. python pipeline/wbr_polish_with_llm.py wbr.txt

API reference: https://docs.claude.com/en/api/overview
"""
import os
import re
import sys

import requests

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
PROMPT = """You are editing a weekly business review for a VP of sales.
Tighten the draft below. Rules: do not change, add, or remove any number, name, or date;
keep the same sections; lead with the single most important point; 250 words or fewer.

{draft}"""


def numbers(text):
    return sorted(re.findall(r"\d[\d,.]*", text))


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python pipeline/wbr_polish_with_llm.py wbr.txt")
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("Set ANTHROPIC_API_KEY first.")
    draft = open(sys.argv[1], encoding="utf-8").read()
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": MODEL, "max_tokens": 1024, "messages": [{"role": "user", "content": PROMPT.format(draft=draft)}]},
        timeout=60,
    )
    resp.raise_for_status()
    edited = "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text")
    missing = set(numbers(draft)) - set(numbers(edited))
    print(edited)
    if missing:
        print(f"\nWARNING: these numbers from the draft are missing in the edit: {sorted(missing)[:10]}", file=sys.stderr)


if __name__ == "__main__":
    main()
