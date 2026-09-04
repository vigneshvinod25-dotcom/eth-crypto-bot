import os
import time
import threading
import ccxt
import pandas as pd
from flask import Flask

app = Flask(__name__)
bot_started = False

def start_bot():
    print("Starting Crypto Bot Loop...")
    
    api_key = os.environ.get('BINANCE_API_KEY')
    secret_key = os.environ.get('BINANCE_SECRET_KEY')

    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': secret_key,
        'enableRateLimit': True,
    })
    
    exchange.set_sandbox_mode(True) 
    
    symbol = 'ETH/USDT'
    timeframe = '5m'
    in_position = False

    while True:
        try:
            bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=50)
            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            
            df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()

            prev_ema9 = df['ema9'].iloc[-3]
            prev_ema21 = df['ema21'].iloc[-3]
            curr_ema9 = df['ema9'].iloc[-2]
            curr_ema21 = df['ema21'].iloc[-2]

            print(f"Checking {symbol}... Prev EMA9: {prev_ema9:.2f}, Prev EMA21: {prev_ema21:.2f} | Curr EMA9: {curr_ema9:.2f}, Curr EMA21: {curr_ema21:.2f}")

            if prev_ema9 < prev_ema21 and curr_ema9 > curr_ema21 and not in_position:
                print("BUY Signal Generated for ETH/USDT!")
                order = exchange.create_market_buy_order(symbol, 0.05)
                print(f"Order Success: {order}")
                in_position = True

            elif prev_ema9 > prev_ema21 and curr_ema9 < curr_ema21 and in_position:
                print("SELL Signal Generated for ETH/USDT!")
                order = exchange.create_market_sell_order(symbol, 0.05)
                print(f"Order Success: {order}")
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
    return "Bot is running 24/7 on Binance Testnet!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
