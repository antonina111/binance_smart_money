import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import fsspec
import numpy as np
from scipy.signal import argrelextrema
import tempfile
from google.cloud import storage

# Config (bucket + prefixes)
BUCKET_NAME = "smart-money-data-lake"
CURATED_PREFIX = "curated/"
ENRICHED_PREFIX = "enriched/"

def main(event, context):
    file_name = event["name"]

    # Only handle Parquet files in curated/
    if not file_name.startswith(CURATED_PREFIX) or not file_name.endswith(".parquet"):
        print(f"Ignoring file: {file_name}")
        return

    print(f"Processing: {file_name}")

    # GCS filesystem via fsspec
    fs = fsspec.filesystem("gcs")

    # Load specific file into DataFrame
    full_path = f"{BUCKET_NAME}/{file_name}"  # no gs://
    with fs.open(full_path, "rb") as f:
        table = pq.read_table(f)
        df = table.to_pandas()

    if df.empty:
        print("No data found in file.")
        return

    # Sort chronologically
    df.sort_values("open_time_ms", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Calculate swing highs/lows
    order = 8
    df["swing_high"] = False
    df["swing_low"] = False

    high_idx = argrelextrema(df["high"].values, np.greater, order=order)[0]
    low_idx = argrelextrema(df["low"].values, np.less, order=order)[0]

    df.loc[df.index[high_idx], "swing_high"] = True
    df.loc[df.index[low_idx], "swing_low"] = True

    # Parse partition info from path
    # curated/symbol=BTCUSDC/date=2025-07-22/data.parquet
    parts = file_name.replace(CURATED_PREFIX, "").split("/")
    symbol = parts[0].split("=")[1]
    date_str = parts[1].split("=")[1]

    output_path = f"{ENRICHED_PREFIX}symbol={symbol}/date={date_str}/data.parquet"

    print(f"Saving enriched file to: {output_path}")

    # Save to temp and upload
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp_file:
        table = pa.Table.from_pandas(df)
        pq.write_table(table, tmp_file.name)
        blob = bucket.blob(output_path)
        blob.upload_from_filename(tmp_file.name)

    print("Enriched file uploaded.")
