-- Whitespace ranking: propensity x first-year land potential for non-customers.
-- Requires sase_gtm.accounts_scored (output of pipeline/propensity_model.py).
DECLARE as_of DATE DEFAULT DATE '2026-09-25';

-- 1. Ranked target list with cumulative share of expected value
SELECT account_id, account_name, segment, region, industry, propensity, land_potential_arr, expected_value,
       DATE_DIFF(ngfw_renewal_date, as_of, DAY) AS days_to_firewall_renewal, play,
       SUM(expected_value) OVER (ORDER BY expected_value DESC ROWS UNBOUNDED PRECEDING)
         / SUM(expected_value) OVER () AS cumulative_share_of_ev
FROM sase_gtm.accounts_scored
WHERE has_prisma_access = 0
ORDER BY expected_value DESC
LIMIT 500;

-- 2. Expected value by play
SELECT play, COUNT(*) AS accounts, SUM(expected_value) AS expected_value
FROM sase_gtm.accounts_scored WHERE has_prisma_access = 0
GROUP BY play ORDER BY expected_value DESC;

-- 3. Renewal-timed attach candidates: top-ranked accounts renewing their firewall in 90 to 270 days
SELECT account_id, account_name, segment, region, expected_value, ngfw_renewal_date
FROM sase_gtm.accounts_scored
WHERE has_prisma_access = 0
  AND DATE_DIFF(ngfw_renewal_date, as_of, DAY) BETWEEN 90 AND 270
ORDER BY expected_value DESC
LIMIT 100;
