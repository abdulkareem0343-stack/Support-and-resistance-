import ccxt
import pandas as pd

# Multi-Exchange Setup (Binance, Bybit, OKX, MEXC, KuCoin)
exchanges = {
    'binance': ccxt.binance(),
    'bybit': ccxt.bybit(),
    'okx': ccxt.okx(),
    'mexc': ccxt.mexc(),
    'kucoin': ccxt.kucoin()
}

# Technical Conditions Check Function
def analyze_candlesticks(df, tolerance_pct=0.5):
    if len(df) < 3:
        return None, None

    prev = df.iloc[-2]  # Choti / Previous Candle
    curr = df.iloc[-1]  # Badi / Current Candle

    # 1. Bullish Engulfing Support (Choti Red Candle -> Badi Green Candle)
    is_prev_bearish = prev['close'] < prev['open']
    is_curr_bullish = curr['close'] > curr['open']
    is_bullish_engulfing = is_prev_bearish and is_curr_bullish and (curr['close'] >= prev['open']) and (curr['open'] <= prev['close'])

    if is_bullish_engulfing:
        support_level = curr['low']
        gap = abs(curr['close'] - support_level) / support_level * 100
        if gap <= tolerance_pct:
            return "SUPPORT_BULLISH_ENGULFING", support_level

    # 2. Bearish Engulfing Resistance (Choti Green Candle -> Badi Red Candle)
    is_prev_bullish = prev['close'] > prev['open']
    is_curr_bearish = curr['close'] < curr['open']
    is_bearish_engulfing = is_prev_bullish and is_curr_bearish and (curr['open'] >= prev['close']) and (curr['close'] <= prev['open'])

    if is_bearish_engulfing:
        resistance_level = curr['high']
        gap = abs(resistance_level - curr['close']) / resistance_level * 100
        if gap <= tolerance_pct:
            return "RESISTANCE_BEARISH_ENGULFING", resistance_level

    return None, None

# Main Execution Loop
timeframes = ['15m', '1h', '4h', '1d']
max_coins_limit = 500  # Total 500 Pairs Tak Scan

total_scanned = 0

print("=== Starting Scan Across Multiple Exchanges ===")

for ex_name, exchange in exchanges.items():
    if total_scanned >= max_coins_limit:
        break
        
    try:
        # Fetch Top Active USDT Markets
        markets = exchange.load_markets()
        usdt_pairs = [symbol for symbol in markets if symbol.endswith('/USDT')][:100]  # Har exchange se top 100 pairs

        print(f"\n[+] Scanning {len(usdt_pairs)} coins on {ex_name.upper()}...")

        for symbol in usdt_pairs:
            if total_scanned >= max_coins_limit:
                break

            for tf in timeframes:
                try:
                    bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=5)
                    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    signal_type, price_level = analyze_candlesticks(df)

                    if signal_type == "SUPPORT_BULLISH_ENGULFING":
                        print(f"🟢 [SUPPORT] Exchange: {ex_name.upper()} | Pair: {symbol} | TF: {tf} | Level: {price_level}")
                    elif signal_type == "RESISTANCE_BEARISH_ENGULFING":
                        print(f"🔴 [RESISTANCE] Exchange: {ex_name.upper()} | Pair: {symbol} | TF: {tf} | Level: {price_level}")

                except Exception:
                    continue
            
            total_scanned += 1

    except Exception as e:
        print(f"Could not load {ex_name}: {e}")

print(f"\n--- Scanning Complete. Total Pairs Processed: {total_scanned} ---")
