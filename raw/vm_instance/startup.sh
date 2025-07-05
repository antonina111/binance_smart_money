#!/bin/bash

set -e

# ===== FETCH CONFIG FROM METADATA =====
CLOUD_FUNCTION_URL=$(curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/cloud-function-url)

# Write the environment variable to a file so systemd can load it
mkdir -p /etc/binance
echo "CLOUD_FUNCTION_URL=$CLOUD_FUNCTION_URL" > /etc/binance/env

# ===== SYSTEM SETUP =====
apt update
apt install -y python3 python3-pip

# ===== SCRIPT SETUP =====
mkdir -p /opt/binance
cd /opt/binance

# Download your Python scripts from metadata
curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/backfill-script > backfill_klines.py

curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/streamer-script > binance_kline_streamer.py

chmod +x *.py

# ===== DEPENDENCIES =====
pip3 install requests websockets

# ===== CREATE SYSTEMD SERVICE =====
cat <<EOF > /etc/systemd/system/binance-streamer.service
[Unit]
Description=Binance Kline Streamer
After=network.target

[Service]
EnvironmentFile=/etc/binance/env
ExecStart=/usr/bin/python3 /opt/binance/binance_kline_streamer.py
Restart=always
User=root
WorkingDirectory=/opt/binance

[Install]
WantedBy=multi-user.target
EOF

# ===== ENABLE AND START SERVICE =====
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable binance-streamer.service
systemctl start binance-streamer.service

echo "✅ Startup script completed"
