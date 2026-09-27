-- Win and loss on first-purchase (land) deals. Competitor win rates in this dataset are synthetic.
CREATE TEMP FUNCTION fiscal_year(d DATE) AS (EXTRACT(YEAR FROM DATE_ADD(d, INTERVAL 5 MONTH)));

CREATE TEMP TABLE land AS
SELECT o.*, a.segment, IF(o.stage = 'Closed Won', 1, 0) AS won
FROM sase_gtm.opportunities o
JOIN sase_gtm.accounts a USING (account_id)
WHERE o.opp_type = 'Land' AND o.stage IN ('Closed Won', 'Closed Lost');

-- 1. FY26 land win rate (count-based)
SELECT COUNT(*) AS closed_deals, AVG(won) AS win_rate FROM land WHERE fiscal_year(close_date) = 2026;

-- 2. Win rate by competitor, with and without SD-WAN in the deal
SELECT competitor, sdwan_bundle, COUNT(*) AS deals, AVG(won) AS win_rate
FROM land GROUP BY competitor, sdwan_bundle ORDER BY competitor, sdwan_bundle;

-- 3. Where lost deals exit, and why
SELECT loss_stage, COUNT(*) AS lost_deals, COUNT(*) / SUM(COUNT(*)) OVER () AS share
FROM land WHERE won = 0 GROUP BY loss_stage ORDER BY lost_deals DESC;

SELECT loss_reason, COUNT(*) AS lost_deals, COUNT(*) / SUM(COUNT(*)) OVER () AS share
FROM land WHERE won = 0 GROUP BY loss_reason ORDER BY lost_deals DESC;

-- 4. What moves win rate (raw). The adjusted SD-WAN effect is estimated in pipeline/propensity_model.py.
SELECT 'SD-WAN in deal vs Zscaler or Netskope' AS factor,
       AVG(IF(sdwan_bundle = 1, won, NULL)) AS win_with, AVG(IF(sdwan_bundle = 0, won, NULL)) AS win_without, COUNT(*) AS deals
FROM land WHERE competitor IN ('Zscaler', 'Netskope')
UNION ALL
SELECT 'Opened 90-270 days before firewall renewal',
       AVG(IF(renewal_aligned = 1, won, NULL)), AVG(IF(renewal_aligned = 0, won, NULL)), COUNT(*) FROM land
UNION ALL
SELECT 'SASE specialist covers territory',
       AVG(IF(specialist_covered = 1, won, NULL)), AVG(IF(specialist_covered = 0, won, NULL)), COUNT(*) FROM land
UNION ALL
SELECT 'Partner-sourced (mid-market and commercial)',
       AVG(IF(source = 'Partner-sourced', won, NULL)), AVG(IF(source != 'Partner-sourced', won, NULL)), COUNT(*)
FROM land WHERE segment IN ('Mid-Market', 'Commercial');
