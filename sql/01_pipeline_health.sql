-- Pipeline health: open pipeline by stage, coverage by FY27 quarter, stalled deals, weekly creation.
-- Mirrors pipeline/metrics.py. Palo Alto Networks' fiscal year starts August 1.
DECLARE as_of DATE DEFAULT DATE '2026-09-25';
DECLARE growth FLOAT64 DEFAULT 0.35;

CREATE TEMP FUNCTION fiscal_year(d DATE) AS (EXTRACT(YEAR FROM DATE_ADD(d, INTERVAL 5 MONTH)));
CREATE TEMP FUNCTION fiscal_quarter(d DATE) AS (EXTRACT(QUARTER FROM DATE_ADD(d, INTERVAL 5 MONTH)));

CREATE TEMP TABLE core AS
SELECT *, fiscal_year(close_date) AS fy, fiscal_quarter(close_date) AS fq
FROM sase_gtm.opportunities
WHERE opp_type IN ('Land', 'Expansion');

-- 1. Open pipeline by stage
SELECT stage, COUNT(*) AS deals, SUM(amount) AS pipeline_arr
FROM core
WHERE stage NOT IN ('Closed Won', 'Closed Lost')
GROUP BY stage
ORDER BY CASE stage WHEN 'Discover' THEN 1 WHEN 'Qualify' THEN 2 WHEN 'Technical Validation' THEN 3
                    WHEN 'Proposal' THEN 4 ELSE 5 END;

-- 2. Coverage by FY27 quarter = open pipeline closing in the quarter / plan still to book
WITH plan AS (
  SELECT SUM(amount) * (1 + growth) AS fy27_target FROM core WHERE stage = 'Closed Won' AND fy = 2026
),
seasonality AS (
  SELECT * FROM UNNEST([STRUCT(1 AS fq, 0.21 AS share), STRUCT(2, 0.26), STRUCT(3, 0.23), STRUCT(4, 0.30)])
),
qtd AS (
  SELECT IFNULL(SUM(amount), 0) AS q1_booked FROM core
  WHERE stage = 'Closed Won' AND close_date BETWEEN DATE '2026-08-01' AND as_of
),
open_pipe AS (
  SELECT fq, SUM(amount) AS pipeline FROM core
  WHERE stage NOT IN ('Closed Won', 'Closed Lost') AND fy = 2027
  GROUP BY fq
),
q AS (
  SELECT s.fq, IFNULL(o.pipeline, 0) AS pipeline,
         p.fy27_target * s.share - IF(s.fq = 1, t.q1_booked, 0) AS remaining_plan
  FROM seasonality s CROSS JOIN plan p CROSS JOIN qtd t LEFT JOIN open_pipe o USING (fq)
)
SELECT CONCAT('FY27 Q', CAST(fq AS STRING)) AS quarter, pipeline, remaining_plan,
       IF(remaining_plan > 0, pipeline / remaining_plan, NULL) AS coverage
FROM q
ORDER BY fq;

-- 3. Deals stalled in Technical Validation past the 45-day SLA
SELECT o.opp_id, a.account_name, a.segment, a.region, o.amount,
       DATE_DIFF(as_of, o.stage_entry_date, DAY) AS days_in_stage, o.competitor, o.push_count, o.close_date
FROM core o
JOIN sase_gtm.accounts a USING (account_id)
WHERE o.stage = 'Technical Validation' AND DATE_DIFF(as_of, o.stage_entry_date, DAY) > 45
ORDER BY o.amount DESC;

-- 4. Pipeline created per week (weeks end Friday) against the trailing 8-week average
WITH weekly AS (
  SELECT DATE_ADD(DATE_TRUNC(created_date, WEEK(SATURDAY)), INTERVAL 6 DAY) AS week_ending,
         COUNT(*) AS deals, SUM(amount) AS created_arr
  FROM core
  WHERE created_date > DATE_SUB(as_of, INTERVAL 34 WEEK) AND created_date <= as_of
  GROUP BY week_ending
)
SELECT week_ending, deals, created_arr,
       AVG(created_arr) OVER (ORDER BY week_ending ROWS BETWEEN 8 PRECEDING AND 1 PRECEDING) AS trailing_8wk_avg,
       SAFE_DIVIDE(created_arr - AVG(created_arr) OVER w8, STDDEV_SAMP(created_arr) OVER w8) AS z_score
FROM weekly
WINDOW w8 AS (ORDER BY week_ending ROWS BETWEEN 8 PRECEDING AND 1 PRECEDING)
ORDER BY week_ending DESC
LIMIT 26;
