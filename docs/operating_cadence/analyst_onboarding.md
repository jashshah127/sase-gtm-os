# Analyst onboarding: first 30 days

A new analyst should be able to own a section of the weekly business review by the end of week two
and present an original finding by day 30. This is the plan I would run.

## Week 1: learn the numbers
- Read the metric dictionary end to end; rebuild three metrics from raw tables in SQL and match them to the dashboard.
- Run the full pipeline locally (`python pipeline/run_all.py`) and read the data-quality report.
- Sit in on the forecast call and the WBR; write down every term you did not know.

## Week 2: own a section
- Take the pipeline-creation section of the WBR. Draft it Tuesday, get feedback Wednesday morning, ship Wednesday.
- Pair on one ad hoc request from a regional leader, start to finish.

## Week 3: go deep on one question
- Pick one territory group with a large coverage gap and explain it: data, deal reviews, two conversations with sellers.

## Week 4: present
- Present one finding to the team in five minutes: the answer first, the evidence second, the ask third.

## Review checklist for any analysis
- Is every metric defined the way the dictionary defines it (denominator, date field, filters)?
- Are the sample sizes shown next to the rates?
- Did the data-quality checks pass for the tables used?
- Could the headline be wrong for a boring reason (seasonality, one large deal, a territory change)?
- Is there a clear so-what: what should someone do differently on Monday?
