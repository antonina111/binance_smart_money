import os
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from google.cloud import storage
import tempfile
import pytz

# Config (single bucket with path-based prefixes)
BUCKET_NAME = "smart-money-data-lake"
RAW_PREFIX = "raw/"
CURATED_PREFIX = "curated/"

def main(event, context):

    file_name = event["name"]
    
    # Only process raw .jsonl files
    if not file_name.startswith(RAW_PREFIX) or not file_name.endswith(".jsonl"):
        print(f"Ignoring non-raw file: {file_name}")
        return

    print(f"Processing raw file: {file_name}")

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)

    try:
        raw_lines = blob.download_as_text().strip().splitlines()
        records = [json.loads(line) for line in raw_lines if line.strip()]
        if not records:
            print("No valid records found.")
            return
        
        df = pd.DataFrame(records)

        # Set Warsaw timezone
        local_tz = pytz.timezone("Europe/Warsaw")
        df["open_time_local"] = [
            datetime.fromtimestamp(ts / 1000, tz=pytz.UTC).astimezone(local_tz).isoformat()
            for ts in df["open_time"]
        ]
        # Rename open_time to open_time_ms
        df.rename(columns={"open_time":"open_time_ms"}, inplace = True)

        # Update symbol to uppercase
        df["symbol"] = df["symbol"].str.upper()

        # Add last_refresh_datetime
        now = datetime.now(local_tz)
        df["last_refresh_datetime"] = now.isoformat()

        order = [
            "exchange",
            "symbol",
            "interval",
            "open_time_ms",
            "open_time_local",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "source",
            "last_refresh_datetime"
        ]
        df = df[order]

        df["date_str"] = pd.to_datetime(df["open_time_ms"], unit="ms", utc=True) \
                    .dt.tz_convert("Europe/Warsaw") \
                    .dt.strftime("%Y-%m-%d")

        # Group data by date
        for date_str, group_df in df.groupby("date_str"):

            symbol = group_df["symbol"].iloc[0]
            output_path = f"{CURATED_PREFIX}symbol={symbol}/date={date_str}/data.parquet"

            print(f"Uploading {len(group_df)} records for {symbol} on {date_str}")
    
            table = pa.Table.from_pandas(group_df.drop(columns=["date_str"]))  # remove date_str column
    
            with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp_file:
                pq.write_table(table, tmp_file.name)
                blob = bucket.blob(output_path)
                blob.upload_from_filename(tmp_file.name)
                print(f"Uploaded Parquet for {date_str} → {output_path}")


        print(f"Successfully processed {file_name} and uploaded Parquet files.")

    except Exception as e:
        print(f"Error processing file {file_name}: {e}")
        raise