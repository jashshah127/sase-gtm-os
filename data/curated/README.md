# Curated public data

Figures in this folder were transcribed by hand from public earnings releases, earnings-call
coverage, and analyst press releases. They are real, but a person (or an AI) typed them, so
**verify every row against its `source_url` before quoting it.**

- `competitor_kpis.csv`: company-reported ARR and related KPIs. Companies define ARR differently:
  Zscaler and Netskope report company-wide ARR; Palo Alto Networks and Fortinet report SASE-specific
  figures. Compare direction and magnitude, not decimals. `primary = 1` marks the row used in the
  growth comparison; `chart_series` groups rows into the ARR-over-time chart.
- `market_context.csv`: Dell'Oro Group SASE market figures. `precision` is `exact`, `approx`
  ("nearly"), or `floor` ("over").

Machine-fetched datasets live in `data/public/` instead (written by `pipeline/fetch_public_data.py`).
Do not mix the two: curated rows are edited by hand, fetched files are regenerated automatically.
