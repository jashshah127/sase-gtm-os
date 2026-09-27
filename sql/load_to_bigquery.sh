#!/usr/bin/env bash
# Load the pipeline's clean tables into BigQuery (the free BigQuery sandbox works).
# Requires the Google Cloud SDK. Run from the repo root:
#   ./sql/load_to_bigquery.sh <gcp-project-id> [dataset]
set -euo pipefail
PROJECT="${1:?usage: ./sql/load_to_bigquery.sh <gcp-project-id> [dataset]}"
DATASET="${2:-sase_gtm}"
bq --project_id="$PROJECT" mk --dataset --location=US "$PROJECT:$DATASET" 2>/dev/null || true
for t in accounts opportunities territories specialists; do
  bq --project_id="$PROJECT" load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
    "$DATASET.$t" "data/clean/$t.csv"
done
bq --project_id="$PROJECT" load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
  "$DATASET.accounts_scored" "data/processed/accounts_scored.csv"
echo "Loaded into $PROJECT:$DATASET. The queries in sql/ reference tables as sase_gtm.<table>."
