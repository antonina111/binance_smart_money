import time
import datetime
import requests
import json
import os

# Binance REST API config
BINANCE_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "BTCUSDC"
INTERVAL = "1h"
DAYS = 30
LIMIT = 1000  # Max candles per request

# GCP Cloud Function URL
CLOUD_FUNCTION_URL = os.environ.get("CLOUD_FUNCTION_URL")
if not CLOUD_FUNCTION_URL:
    try:
        CLOUD_FUNCTION_URL = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/attributes/cloud-function-url",
            headers={"Metadata-Flavor": "Google"},
            timeout=2
        ).text
    except Exception:
        raise ValueError("CLOUD_FUNCTION_URL not set and cannot be fetched from metadata")

print(CLOUD_FUNCTION_URL)

def get_klines(start_time, end_time):
    """Fetch klines from Binance API within a given time range."""
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "startTime": int(start_time.timestamp() * 1000),
        "endTime": int(end_time.timestamp() * 1000) - 1,
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
    now = datetime.datetime.now(datetime.timezone.utc)
    now = now.replace(minute=0, second=0, microsecond=0)
    start = now - datetime.timedelta(days=DAYS)

    print(f"Starting backfill from {start} to {now}...")

    all_klines = []
    batch_start = start

    while batch_start < now:
        batch_end = min(batch_start + datetime.timedelta(hours=LIMIT), now)

        try:
            klines = get_klines(batch_start, batch_end)
            if klines:
                enriched_klines = []
                for kline in klines:
                    enriched_kline = {
                        "exchange": "Binance",
                        "symbol": SYMBOL,
                        "interval": INTERVAL,
                        "open_time": kline[0],
                        "open": kline[1],
                        "high": kline[2],
                        "low": kline[3],
                        "close": kline[4],
                        "volume": kline[5],
                        "source": "rest"
                    }
                    enriched_klines.append(enriched_kline)
                all_klines.extend(enriched_klines)
                print(f"Collected {len(klines)} klines from {batch_start} to {batch_end}")
            else:
                print(f"No data for {batch_start} → {batch_end}")
        except Exception as e:
            print(f"Error for {batch_start} → {batch_end}: {e}")

        batch_start = batch_end
        time.sleep(0.2)  # Sleep to avoid rate limits

    print(f"Sending total {len(all_klines)} klines to Cloud Function...")
    print("Sending to:", CLOUD_FUNCTION_URL)
    send_to_gcp(all_klines)

    print("Backfill complete.")