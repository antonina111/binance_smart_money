#!/bin/bash
set -e

# ===== LOAD CONFIG =====
if [ ! -f .env ]; then
  echo ".env file not found! Create one with:"
  echo "BUCKET_NAME=your-bucket-name"
  exit 1
fi

source .env

# Name of the Cloud Function on GCP
FUNCTION_NAME="binance-raw-loader"
# Name of the function inside main.py
ENTRY_POINT="main"
# GCP region
REGION="europe-west3"

echo "Deploying Cloud Function: $FUNCTION_NAME to $REGION..."

# Deploy it
gcloud functions deploy "$FUNCTION_NAME" \
  --region "$REGION" \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point "$ENTRY_POINT" \
  --source=. \
  --set-env-vars BUCKET_NAME="$BUCKET_NAME"


echo "Deployment complete."