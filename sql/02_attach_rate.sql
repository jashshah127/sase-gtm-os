-- SASE attach: share of NGFW accounts that own Prisma Access, by scope and over time.
DECLARE as_of DATE DEFAULT DATE '2026-09-25';

-- 1. Attach by region, segment, and industry (ROLLUP adds subtotals; NULL = all)
SELECT region, segment, industry, COUNT(*) AS accounts, COUNTIF(has_prisma_access = 1) AS customers,
       SAFE_DIVIDE(COUNTIF(has_prisma_access = 1), COUNT(*)) AS attach_rate,
       SUM(sase_arr + browser_arr) AS sase_arr
FROM sase_gtm.accounts
GROUP BY ROLLUP (region, segment, industry)
ORDER BY region NULLS FIRST, segment NULLS FIRST, industry NULLS FIRST;

-- 2. Attach rate at each fiscal quarter end, FY24 Q1 to date
WITH quarter_ends AS (
  SELECT LEAST(DATE_SUB(DATE_ADD(q, INTERVAL 3 MONTH), INTERVAL 1 DAY), as_of) AS quarter_end
  FROM UNNEST(GENERATE_DATE_ARRAY(DATE '2023-08-01', DATE '2026-08-01', INTERVAL 3 MONTH)) AS q
)
SELECT quarter_end,
       CONCAT('FY', FORMAT_DATE('%y', DATE_ADD(quarter_end, INTERVAL 5 MONTH)),
              ' Q', CAST(EXTRACT(QUARTER FROM DATE_ADD(quarter_end, INTERVAL 5 MONTH)) AS STRING)) AS fiscal_quarter,
       SAFE_DIVIDE(COUNTIF(a.sase_first_purchase_date <= quarter_end), COUNT(*)) AS attach_rate
FROM quarter_ends CROSS JOIN sase_gtm.accounts a
GROUP BY quarter_end
ORDER BY quarter_end;
