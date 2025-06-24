import datetime
import pandas as pd
from google.cloud import storage
import functions_framework
import io

# GCS Configuration
BUCKET_NAME = "binance-data-l"
DESTINATION_BLOB_NAME = "raw/binance_btcusdc_1h.csv"

# Convert raw klines (list of lists) to list of dicts
def format_klines(raw_klines):
    return [
        {
            "open_time": datetime.datetime.fromtimestamp(row[0] / 1000),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5])
        }
        for row in raw_klines
    ]

@functions_framework.http
def main(request):
    try:
        req_json = request.get_json()

        # Accept either single kline or list of klines
        klines = req_json.get("klines")
        single_kline = req_json.get("kline")

        if klines:
            formatted = format_klines(klines)
        elif single_kline:
            formatted = format_klines([single_kline])
        else:
            return "No 'kline' or 'klines' provided in request", 400

        new_df = pd.DataFrame(formatted)

        # GCS client and blob
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(DESTINATION_BLOB_NAME)

        # Load existing CSV if present
        if blob.exists():
            existing_csv = blob.download_as_text()
            existing_df = pd.read_csv(io.StringIO(existing_csv), parse_dates=["open_time"])

            # Merge, deduplicate, sort
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df.drop_duplicates(subset="open_time", keep="last", inplace=True)
            combined_df.sort_values("open_time", inplace=True)
        else:
            combined_df = new_df

        # Upload updated CSV
        blob.upload_from_string(combined_df.to_csv(index=False), content_type="text/csv")

        return f"Appended {len(new_df)} kline(s)", 200

    except Exception as e:
        return f"Error: {e}", 500
