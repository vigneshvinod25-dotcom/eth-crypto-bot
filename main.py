import os
import json
import time
import threading
import requests
import websocket
import pandas as pd
from flask import Flask

app = Flask(__name__)
bot_started = False

candles = []

def send_telegram_msg(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Telegram Error: {e}", flush=True)

def process_signals():
    global candles
    in_position = False
    
    while True:
        if len(candles) >= 21:
            df = pd.DataFrame(candles, columns=['close'])
            df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()

            prev_ema9 = df['ema9'].iloc[-3]
            prev_ema21 = df['ema21'].iloc[-3]
            curr_ema9 = df['ema9'].iloc[-2]
            curr_ema21 = df['ema21'].iloc[-2]
            last_price = df['close'].iloc[-1]

            if prev_ema9 < prev_ema21 and curr_ema9 > curr_ema21 and not in_position:
                msg = f"🟢 BUY SIGNAL! (ETH/USDT)\nPrice: ${last_price:.2f}\nEMA 9 crossed above EMA 21."
                print(msg, flush=True)
                send_telegram_msg(msg)
                in_position = True

            elif prev_ema9 > prev_ema21 and curr_ema9 < curr_ema21 and in_position:
                msg = f"🔴 SELL SIGNAL! (ETH/USDT)\nPrice: ${last_price:.2f}\nEMA 9 crossed below EMA 21."
                print(msg, flush=True)
                send_telegram_msg(msg)
                in_position = False

        time.sleep(10)

def on_message(ws, message):
    global candles
    data = json.loads(message)
    kline = data['k']
    is_candle_closed = kline['x']
    close_price = float(kline['c'])

    # Live ticker output on every single price tick
    print(f"Live Price: ${close_price:.2f}", flush=True)

    if is_candle_closed:
        candles.append(close_price)
        if len(candles) > 50:
            candles.pop(0)

        if len(candles) >= 21:
            df = pd.DataFrame(candles, columns=['close'])
            df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
            
            curr_ema9 = df['ema9'].iloc[-1]
            curr_ema21 = df['ema21'].iloc[-1]
            
            print(f"--- CANDLE CLOSED --- Price: ${close_price:.2f} | EMA9: {curr_ema9:.2f} | EMA21: {curr_ema21:.2f}", flush=True)
        else:
            print(f"--- CANDLE CLOSED --- Price: ${close_price:.2f} | Collecting ({len(candles)}/21)...", flush=True)

def start_websocket():
    print("Starting Binance WebSocket Stream...", flush=True)
    send_telegram_msg("🚀 WebSocket Signal Bot Active!")

    threading.Thread(target=process_signals, daemon=True).start()

    socket_url = "wss://stream.binance.com:9443/ws/ethusdt@kline_5m"
    
    ws = websocket.WebSocketApp(
        socket_url,
        on_message=on_message,
        on_error=lambda ws, err: print(f"WS Error: {err}", flush=True),
        on_close=lambda ws, status, msg: print("WS Closed", flush=True)
    )
    ws.run_forever()

@app.before_request
def init_bot():
    global bot_started
    if not bot_started:
        bot_started = True
        t = threading.Thread(target=start_websocket)
        t.daemon = True
        t.start()

@app.route('/')
def home():
    return "WebSocket Signal Bot Running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
