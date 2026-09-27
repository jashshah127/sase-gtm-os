-- SASE GTM Operating System: warehouse schema (BigQuery Standard SQL).
-- Grain and definitions: docs/methodology.md and docs/operating_cadence/metric_dictionary.md.
-- load_to_bigquery.sh creates these tables from the CSVs; this DDL documents the model.
CREATE SCHEMA IF NOT EXISTS sase_gtm;

CREATE OR REPLACE TABLE sase_gtm.accounts (
  account_id STRING NOT NULL, account_name STRING, industry STRING, segment STRING, region STRING, country STRING,
  employees INT64, branch_count INT64, remote_workforce_pct FLOAT64, contractor_pct FLOAT64,
  unmanaged_device_pct FLOAT64, vdi_in_use INT64, incumbent_remote_access STRING,
  cortex_xdr INT64, cortex_cloud INT64, health_score INT64, customer_since INT64, ngfw_arr FLOAT64,
  ngfw_renewal_date DATE, renewal_term_months INT64, full_potential_arr FLOAT64, land_potential_arr FLOAT64,
  territory_id STRING, specialist_covered INT64, has_prisma_access INT64, has_prisma_sdwan INT64,
  sase_first_purchase_date DATE, sase_arr FLOAT64, has_prisma_browser INT64, browser_arr FLOAT64,
  browser_early_adopter INT64
);

CREATE OR REPLACE TABLE sase_gtm.opportunities (
  opp_id STRING NOT NULL, account_id STRING NOT NULL, opp_type STRING, product STRING,
  created_date DATE, close_date DATE, stage STRING, amount FLOAT64, competitor STRING, sdwan_bundle INT64,
  source STRING, loss_reason STRING, loss_stage STRING, stage_entry_date DATE, push_count INT64,
  last_push_date DATE, renewal_aligned INT64, specialist_covered INT64, pov_start_date DATE
);

CREATE OR REPLACE TABLE sase_gtm.territories (
  territory_id STRING NOT NULL, region STRING, segment STRING, account_count INT64,
  specialist_covered INT64, specialist_id STRING
);

CREATE OR REPLACE TABLE sase_gtm.specialists (
  specialist_id STRING NOT NULL, specialist_name STRING, region STRING, segment STRING, hire_date DATE
);

-- accounts_scored = accounts + model outputs (propensity, expected_value, play, icp_score, icp_tier),
-- produced by pipeline/propensity_model.py and loaded with schema autodetect.
