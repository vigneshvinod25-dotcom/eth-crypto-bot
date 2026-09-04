import os
import time
import threading
import ccxt
import pandas as pd
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7 on Binance Testnet!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

def start_bot():
    exchange = ccxt.binance({
        'apiKey': '8vT8K69pO2cppwXacKTx0UYgYCLaxEoBAMdd3ur0e4rb1TVuasN66eJPIaYkDdxL',
        'secret': 'HkDJtlVYlf5sncC1Fi4Y95A3JX8WAcsUI0VBjCEzloP3K0G5NBDlOQFdfguyvh3QY',
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
            
            # pandas മാത്രം ഉപയോഗിച്ച് EMA കണക്കാക്കുന്നു (pandas_ta ആവശ്യമില്ല)
            df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()

            prev_ema9 = df['ema9'].iloc[-3]
            prev_ema21 = df['ema21'].iloc[-3]
            curr_ema9 = df['ema9'].iloc[-2]
            curr_ema21 = df['ema21'].iloc[-2]

            if prev_ema9 < prev_ema21 and curr_ema9 > curr_ema21 and not in_position:
                print("BUY Signal Generated for ETH/USDT!")
                order = exchange.create_market_buy_order(symbol, 0.05)
                print(order)
                in_position = True

            elif prev_ema9 > prev_ema21 and curr_ema9 < curr_ema21 and in_position:
                print("SELL Signal Generated for ETH/USDT!")
                order = exchange.create_market_sell_order(symbol, 0.05)
                print(order)
                in_position = False

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(60)

if __name__ == "__main__":
    t = threading.Thread(target=start_bot)
    t.start()
    run_flask()
