import asyncio
import websockets
import json
import requests

# Configuration
SYMBOL = "btcusdc"
INTERVAL = "1h"
STREAM_URL = f"wss://stream.binance.com:9443/ws/{SYMBOL}@kline_{INTERVAL}"
CLOUD_FUNCTION_URL = "https://europe-west3-mineral-brand-231612.cloudfunctions.net/binance-raw-loader"

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
                print("Kline closed. Sending to Cloud Function...")

                formatted_kline = {
                    "exchange": "Binance",
                    "symbol": SYMBOL,
                    "interval": INTERVAL,
                    "open_time": kline["t"],
                    "open": kline["o"],
                    "high": kline["h"],
                    "low": kline["l"],
                    "close": kline["c"],
                    "volume": kline["v"],
                    "source": "websocket"
                }
                #send_to_gcp(formatted_kline)
                json_send={"kline": formatted_kline}
                print(json_send)

if __name__ == "__main__":
    asyncio.run(stream_kline())