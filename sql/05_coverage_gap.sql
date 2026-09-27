-- Coverage gap: modeled attach (look-alike propensity) vs actual attach.
-- Latent customers = sum of propensity - actual customers. Near zero in covered territories by construction.

-- 1. By territory
SELECT territory_id, region, segment, MAX(specialist_covered) AS specialist_covered, COUNT(*) AS accounts,
       AVG(has_prisma_access) AS actual_attach, AVG(propensity) AS modeled_attach,
       SUM(propensity) - SUM(has_prisma_access) AS latent_customers
FROM sase_gtm.accounts_scored
GROUP BY territory_id, region, segment
ORDER BY latent_customers DESC;

-- 2. By region and segment
SELECT region, segment, COUNT(*) AS accounts, AVG(specialist_covered) AS covered_share,
       AVG(has_prisma_access) AS actual_attach, AVG(propensity) AS modeled_attach,
       ROUND((AVG(propensity) - AVG(has_prisma_access)) * 100, 1) AS gap_pts
FROM sase_gtm.accounts_scored
GROUP BY region, segment
ORDER BY gap_pts DESC;
