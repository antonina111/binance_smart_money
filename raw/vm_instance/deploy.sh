#!/bin/bash

# ===== VM CONFIGURATION =====
VM_NAME="binance-fetcher-vm"
ZONE="europe-west3-a"
MACHINE_TYPE="e2-micro"
IMAGE_FAMILY="debian-11"
IMAGE_PROJECT="debian-cloud"
BOOT_DISK_SIZE="10GB"
STARTUP_SCRIPT="startup.sh"

# ===== LOAD LOCAL SECRETS =====
if [ ! -f .env ]; then
  echo ".env file not found! Create one with your config:"
  echo "CLOUD_FUNCTION_URL=..."
  echo "SYMBOL=BTCUSDC"
  echo "INTERVAL=1h"
  echo "DAYS=30"
  exit 1
fi

# Load .env file
source .env

# ===== DEPLOY THE VM =====
#echo "Deploying GCP VM: $VM_NAME..."

#gcloud compute instances create "$VM_NAME" \
#  --zone="$ZONE" \
#  --machine-type="$MACHINE_TYPE" \
#  --metadata-from-file startup-script="$STARTUP_SCRIPT",backfill-script=backfill_klines.py,streamer-script=binance_kline_streamer.py \
#  --image-family="$IMAGE_FAMILY" \
#  --image-project="$IMAGE_PROJECT" \
#  --boot-disk-size="$BOOT_DISK_SIZE" \
#  --tags=binance-fetcher \
#  --quiet

#echo "VM deployment complete. You can now SSH with:"
#echo "  gcloud compute ssh $VM_NAME --zone=$ZONE"


#Redeploy scripts
gcloud compute instances add-metadata "$VM_NAME" \
  --zone "$ZONE" \
  --metadata-from-file startup-script="$STARTUP_SCRIPT"

# Upload backfill script
gcloud compute instances add-metadata "$VM_NAME" \
  --zone "$ZONE" \
  --metadata-from-file backfill-script=backfill_klines.py

# Upload streamer script
gcloud compute instances add-metadata "$VM_NAME" \
  --zone "$ZONE" \
  --metadata-from-file streamer-script=binance_kline_streamer.py

gcloud compute instances add-metadata "$VM_NAME" \
  --zone "$ZONE" \
  --metadata \
    cloud-function-url="$CLOUD_FUNCTION_URL"

echo "Scripts redeployed"
