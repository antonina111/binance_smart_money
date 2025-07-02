#!/bin/bash

# Update and install Python + pip
apt update
apt install -y python3 python3-pip

# Make a directory for your script
mkdir -p /opt/binance
cd /opt/binance

curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/backfill-script" \
  -H "Metadata-Flavor: Google" > backfill_klines.py

curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/streamer-script" \
  -H "Metadata-Flavor: Google" > binance_kline_streamer.py

# Install dependencies (e.g., requests)
pip3 install requests websockets

# Create a systemd service for the streamer
cat <<EOF > /etc/systemd/system/binance-streamer.service
[Unit]
Description=Binance Kline Streamer
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/binance/binance_kline_streamer.py
Restart=always
User=root
WorkingDirectory=/opt/binance

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable binance-streamer.service
systemctl start binance-streamer.service

echo "✅ Startup script completed"