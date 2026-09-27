-- Specialist capacity: ramp status, FY26 productivity per ramped specialist, and coverage load.
-- Productivity = FY26 covered-territory bookings / average ramped FTE (6-month linear ramp, mid-month).
DECLARE as_of DATE DEFAULT DATE '2026-09-25';
CREATE TEMP FUNCTION fiscal_year(d DATE) AS (EXTRACT(YEAR FROM DATE_ADD(d, INTERVAL 5 MONTH)));

-- 1. Productivity per ramped specialist
WITH months AS (
  SELECT m FROM UNNEST(GENERATE_DATE_ARRAY(DATE '2025-08-15', DATE '2026-07-15', INTERVAL 1 MONTH)) AS m
),
ramped AS (
  SELECT m, SUM(LEAST(1, GREATEST(0, DATE_DIFF(m, s.hire_date, DAY) / 30.4 / 6))) AS ramped_fte
  FROM months CROSS JOIN sase_gtm.specialists s
  GROUP BY m
),
covered AS (
  SELECT SUM(amount) AS covered_bookings
  FROM sase_gtm.opportunities
  WHERE stage = 'Closed Won' AND opp_type IN ('Land', 'Expansion')
    AND specialist_covered = 1 AND fiscal_year(close_date) = 2026
)
SELECT c.covered_bookings, AVG(r.ramped_fte) AS avg_ramped_fte,
       ROUND(c.covered_bookings / AVG(r.ramped_fte), -3) AS productivity_per_ramped_specialist
FROM covered c CROSS JOIN ramped r
GROUP BY c.covered_bookings;

-- 2. Specialists still ramping as of today
SELECT specialist_id, specialist_name, region, segment, hire_date,
       LEAST(1, DATE_DIFF(as_of, hire_date, DAY) / 30.4 / 6) AS ramp_factor
FROM sase_gtm.specialists
WHERE DATE_DIFF(as_of, hire_date, DAY) / 30.4 < 6
ORDER BY hire_date DESC;

-- 3. Coverage load: accounts per specialist by region and segment
SELECT t.region, t.segment, SUM(t.account_count) AS accounts,
       SUM(IF(t.specialist_covered = 1, t.account_count, 0)) AS covered_accounts,
       COUNT(DISTINCT NULLIF(t.specialist_id, '')) AS specialists,
       SAFE_DIVIDE(SUM(IF(t.specialist_covered = 1, t.account_count, 0)),
                   COUNT(DISTINCT NULLIF(t.specialist_id, ''))) AS accounts_per_specialist
FROM sase_gtm.territories t
GROUP BY t.region, t.segment
ORDER BY t.region, t.segment;
