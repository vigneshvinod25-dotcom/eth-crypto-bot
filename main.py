import os
import time
import threading
import ccxt
import requests
import pandas as pd
from flask import Flask

app = Flask(__name__)
bot_started = False

def send_telegram_msg(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Telegram Error: {e}")

def start_bot():
    print("Starting Telegram Signal Bot...")
    send_telegram_msg("🚀 Crypto Signal Bot Started on Real Binance Data!")

    # Real Binance API (Public Data - No Keys Required)
    exchange = ccxt.binance({'enableRateLimit': True})
    
    symbol = 'ETH/USDT'
    timeframe = '5m'
    in_position = False

    while True:
        try:
            bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=50)
            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            
            if len(df) >= 3:
                df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
                df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()

                prev_ema9 = df['ema9'].iloc[-3]
                prev_ema21 = df['ema21'].iloc[-3]
                curr_ema9 = df['ema9'].iloc[-2]
                curr_ema21 = df['ema21'].iloc[-2]
                last_price = df['close'].iloc[-1]

                print(f"Checking {symbol}... EMA9: {curr_ema9:.2f} | EMA21: {curr_ema21:.2f}")

                # BUY SIGNAL
                if prev_ema9 < prev_ema21 and curr_ema9 > curr_ema21 and not in_position:
                    msg = f"🟢 BUY SIGNAL! (ETH/USDT)\nPrice: ${last_price:.2f}\nEMA 9 crossed above EMA 21."
                    print(msg)
                    send_telegram_msg(msg)
                    in_position = True

                # SELL SIGNAL
                elif prev_ema9 > prev_ema21 and curr_ema9 < curr_ema21 and in_position:
                    msg = f"🔴 SELL SIGNAL! (ETH/USDT)\nPrice: ${last_price:.2f}\nEMA 9 crossed below EMA 21."
                    print(msg)
                    send_telegram_msg(msg)
                    in_position = False

        except Exception as e:
            print(f"Error in bot loop: {e}")

        time.sleep(60)

@app.before_request
def init_bot():
    global bot_started
    if not bot_started:
        bot_started = True
        t = threading.Thread(target=start_bot)
        t.daemon = True
        t.start()

@app.route('/')
def home():
    return "Telegram Signal Bot is Active!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
