import time
import datetime
import requests
import json

# Binance REST API config
BINANCE_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "BTCUSDC"
INTERVAL = "1h"
DAYS = 30
LIMIT = 1000  # Max candles per request

# GCP Cloud Function URL (replace with your actual deployed function)
CLOUD_FUNCTION_URL = "https://binance-raw-504389925601.europe-west3.run.app"

def get_klines(start_time, end_time):
    """Fetch klines from Binance API within a given time range."""
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "startTime": int(start_time.timestamp() * 1000),
        "endTime": int(end_time.timestamp() * 1000),
        "limit": LIMIT
    }

    response = requests.get(BINANCE_URL, params=params)
    response.raise_for_status()
    return response.json()

def send_to_gcp(data):
    """Send kline batch to the GCP Cloud Function."""
    headers = {"Content-Type": "application/json"}
    response = requests.post(CLOUD_FUNCTION_URL, json={"klines": data}, headers=headers)
    print(f"Sent {len(data)} klines → Status: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    now = datetime.datetime.utcnow()
    start = now - datetime.timedelta(days=DAYS)

    print(f"Starting backfill from {start} to {now}...")

    all_klines = []
    batch_start = start

    while batch_start < now:
        batch_end = min(batch_start + datetime.timedelta(hours=LIMIT), now)

        try:
            klines = get_klines(batch_start, batch_end)
            if klines:
                all_klines.extend(klines)
                print(f"Collected {len(klines)} klines from {batch_start} to {batch_end}")
            else:
                print(f"No data for {batch_start} → {batch_end}")
        except Exception as e:
            print(f"Error for {batch_start} → {batch_end}: {e}")

        batch_start = batch_end
        time.sleep(0.2)  # Sleep to avoid rate limits

    print(f"Sending total {len(all_klines)} klines to Cloud Function...")
    send_to_gcp(all_klines)

    print("Backfill complete.")
