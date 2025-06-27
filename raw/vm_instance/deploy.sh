#!/bin/bash

# ===== VM CONFIGURATION =====
VM_NAME="binance-fetcher-vm"
ZONE="europe-west3-a"
MACHINE_TYPE="e2-micro"
IMAGE_FAMILY="debian-11"
IMAGE_PROJECT="debian-cloud"
BOOT_DISK_SIZE="10GB"
STARTUP_SCRIPT="startup.sh"

# ===== DEPLOY THE VM =====
echo "Deploying GCP VM: $VM_NAME..."

gcloud compute instances create "$VM_NAME" \
  --zone="$ZONE" \
  --machine-type="$MACHINE_TYPE" \
  --metadata-from-file startup-script="$STARTUP_SCRIPT",backfill-script=backfill_klines.py,streamer-script=binance_kline_streamer.py \
  --image-family="$IMAGE_FAMILY" \
  --image-project="$IMAGE_PROJECT" \
  --boot-disk-size="$BOOT_DISK_SIZE" \
  --tags=binance-fetcher \
  --quiet

echo "VM deployment complete. You can now SSH with:"
echo "  gcloud compute ssh $VM_NAME --zone=$ZONE"
