#!/bin/bash
set -e

# === CONFIG ===
PROJECT_ID="mineral-brand-231612"
DATASET_ID="smart_money"
TABLE_ID="enriched_btcusdc"
TABLE_DEF_FILE="enriched_btcusdc_external.json"
LOCATION="europe-west3"

# === CREATE DATASET IF NOT EXISTS ===
bq --location="${LOCATION}" mk --dataset "${PROJECT_ID}:${DATASET_ID}" || true

# === CREATE EXTERNAL TABLE FROM JSON DEF ===
bq mk \
  --location="${LOCATION}" \
  --external_table_definition="${TABLE_DEF_FILE}" \
  --project_id="${PROJECT_ID}" \
  "${DATASET_ID}.${TABLE_ID}"

echo "External table '${DATASET_ID}.${TABLE_ID}' created in '${LOCATION}' from bucket"
