from google.cloud import storage
import functions_framework
import json

# GCS Configuration
BUCKET_NAME = "smart-money-data-lake"
DESTINATION_BLOB_NAME = "raw/binance_btcusdc_1h.jsonl"
STREAMING_TEMP_BLOB = "raw/btcusdc_1h_temp.jsonl"


@functions_framework.http
def main(request):
    try:
        req_json = request.get_json()

        # Accept either single kline or list of klines
        klines = req_json.get("klines")
        single_kline = req_json.get("kline")

        # GCS client and blob
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(DESTINATION_BLOB_NAME)

        # If streaming, use a temporary blob
        if single_kline:
            temp_blob = bucket.blob(STREAMING_TEMP_BLOB)

            if isinstance(single_kline, dict):
                single_kline = json.dumps(single_kline, separators=(",", ":")) + "\n"

            temp_blob.upload_from_string(
                single_kline,
                content_type="application/json"
            )
            # Compose the original and the new blob
            if blob.exists():
                blob.compose([blob, temp_blob])
                # Delete the temporary blob
                temp_blob.delete()

                return "Single kline appended successfully to existing file", 200
            else:
                # If the destination blob doesn't exist, just rename the temp blob
                bucket.copy_blob(temp_blob, bucket, DESTINATION_BLOB_NAME)
                temp_blob.delete()

                return "Single kline appended successfully to new file", 200

        elif klines:
            
            existing_open_times = set()
            existing_lines = []

            if blob.exists():
                content = blob.download_as_text().splitlines()
                for line in content:
                    record = json.loads(line)
                    existing_open_times.add(record.get("open_time"))
                    existing_lines.append(line)

            # Append only new lines (deduped by open_time)
            new_lines = []
            for row in klines:
                if row.get("open_time") not in existing_open_times:
                    new_lines.append(json.dumps(row, separators=(",", ":")))

            combined_lines = existing_lines + new_lines
            # Sort combined lines by open_time
            combined_lines.sort(key=lambda x: json.loads(x)["open_time"])
            # Write the combined lines back to the blob
            blob.upload_from_string("\n".join(combined_lines), content_type="application/json")

            return f"Appended {len(new_lines)} new kline(s)", 200

        else:
            
            return "No 'kline' or 'klines' provided in request", 400

    except Exception as e:
        return f"Error: {e}", 500
