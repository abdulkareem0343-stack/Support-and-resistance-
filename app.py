import streamlit as st
import ccxt
import pandas as pd

st.set_page_config(page_title="Crypto Scanner", layout="wide")
st.title("📊 Multi-Exchange Engulfing Scanner")

# Multi-Exchange Setup
exchanges = {
    'binance': ccxt.binance(),
    'bybit': ccxt.bybit(),
    'okx': ccxt.okx(),
    'mexc': ccxt.mexc(),
    'kucoin': ccxt.kucoin()
}

def analyze_candlesticks(df, tolerance_pct=0.5):
    if len(df) < 3:
        return None, None

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    # 1. Bullish Engulfing Support
    is_prev_bearish = prev['close'] < prev['open']
    is_curr_bullish = curr['close'] > curr['open']
    is_bullish_engulfing = is_prev_bearish and is_curr_bullish and (curr['close'] >= prev['open']) and (curr['open'] <= prev['close'])

    if is_bullish_engulfing:
        support_level = curr['low']
        gap = abs(curr['close'] - support_level) / support_level * 100
        if gap <= tolerance_pct:
            return "SUPPORT_BULLISH_ENGULFING", support_level

    # 2. Bearish Engulfing Resistance
    is_prev_bullish = prev['close'] > prev['open']
    is_curr_bearish = curr['close'] < curr['open']
    is_bearish_engulfing = is_prev_bullish and is_curr_bearish and (curr['open'] >= prev['close']) and (curr['close'] <= prev['open'])

    if is_bearish_engulfing:
        resistance_level = curr['high']
        gap = abs(resistance_level - curr['close']) / resistance_level * 100
        if gap <= tolerance_pct:
            return "RESISTANCE_BEARISH_ENGULFING", resistance_level

    return None, None

# UI Controls
timeframe = st.selectbox("Select Timeframe", ['15m', '1h', '4h', '1d'], index=1)
tolerance = st.slider("Tolerance Gap (%)", 0.1, 2.0, 0.5)

if st.button("🚀 Start Scanning"):
    st.info("Scanning started across exchanges...")
    results = []
    
    for ex_name, exchange in exchanges.items():
        try:
            markets = exchange.load_markets()
            usdt_pairs = [symbol for symbol in markets if symbol.endswith('/USDT')][:50]
            
            for symbol in usdt_pairs:
                try:
                    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=5)
                    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    signal, price = analyze_candlesticks(df, tolerance_pct=tolerance)
                    if signal:
                        results.append({
                            "Exchange": ex_name.upper(),
                            "Pair": symbol,
                            "Timeframe": timeframe,
                            "Type": "🟢 Support" if "SUPPORT" in signal else "🔴 Resistance",
                            "Price Level": price
                        })
                except Exception:
                    continue
        except Exception:
            continue

    if results:
        res_df = pd.DataFrame(results)
        st.success(f"Found {len(results)} signals!")
        st.dataframe(res_df, use_container_width=True)
    else:
        st.warning("No signals found for the selected timeframe.")
