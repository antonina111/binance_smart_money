import asyncio
import websockets
import json
import requests

# Configuration
SYMBOL = "btcusdc"
INTERVAL = "1h"
STREAM_URL = f"wss://stream.binance.com:9443/ws/{SYMBOL}@kline_{INTERVAL}"
CLOUD_FUNCTION_URL = "https://binance-raw-504389925601.europe-west3.run.app"

def send_to_gcp(data):
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(CLOUD_FUNCTION_URL, json={"kline": data}, headers=headers)
        print(f"[GCP] Status: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[GCP Error] {e}")

async def stream_kline():
    async with websockets.connect(STREAM_URL) as websocket:
        print(f"Connected to Binance WebSocket for {SYMBOL.upper()} {INTERVAL} klines.")
        while True:
            message = await websocket.recv()
            kline_data = json.loads(message)
            kline = kline_data.get("k", {})

            if kline.get("x"):  # Only send closed candles
                print("⏳ Kline closed. Sending to Cloud Function...")

                formatted_kline = [
                    kline["t"],
                    kline["o"],
                    kline["h"],
                    kline["l"],
                    kline["c"],
                    kline["v"],
                ]
                send_to_gcp(formatted_kline)

if __name__ == "__main__":
    asyncio.run(stream_kline())

