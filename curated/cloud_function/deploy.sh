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
FUNCTION_NAME="binance-curated-loader"
ENTRY_POINT="main"
REGION="europe-west3"

echo "Deploying Cloud Function: $FUNCTION_NAME to $REGION..."

gcloud functions deploy "$FUNCTION_NAME" \
  --region "$REGION" \
  --runtime python310 \
  --trigger-resource "$BUCKET_NAME" \
  --trigger-event google.storage.object.finalize \
  --entry-point "$ENTRY_POINT" \
  --source=. \
  --memory=512MB \
  --set-env-vars BUCKET_NAME="$BUCKET_NAME"

echo "Deployment complete."