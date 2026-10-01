import streamlit as st
import ccxt
import pandas as pd

# Page Setup
st.set_page_config(page_title="Crypto Multi-Exchange Scanner", layout="wide")

# Styling for Cards/Boxes
st.markdown("""
    <style>
    .stMetric {
        background-color: #1e222d;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #2a2e39;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Multi-Exchange Crypto Scanner")

# Fixed Exchanges Map (Correct CCXT Attributes)
EXCHANGES_MAP = {
    'Binance': ccxt.binance,
    'Bybit': ccxt.bybit,
    'OKX': ccxt.okx,
    'MEXC': ccxt.mexc,
    'KuCoin': ccxt.kucoin,
    'Gate.io': ccxt.gate,   # Fixed: 'gateio' replaced with 'gate'
    'Bitget': ccxt.bitget,
    'BingX': ccxt.bingx
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

# Input Settings Controls
st.subheader("⚙️ Scan Settings")
selected_exchanges = st.multiselect("Exchanges Choose Karein", list(EXCHANGES_MAP.keys()), default=['Binance', 'Bybit', 'OKX', 'MEXC'])
timeframe = st.selectbox("Timeframe", ['15m', '1h', '4h', '1d'], index=1)
tolerance = st.slider("Tolerance Gap (%)", 0.1, 2.0, 0.5)
max_coins_per_ex = st.number_input("Total Coins Limit (Per Exchange)", min_value=5, max_value=500, value=50, step=5)

st.markdown("---")

# Top 3 Advanced Summary Boxes
col1, col2, col3 = st.columns(3)
with col1:
    box_total = st.empty()
    box_total.metric(label="TOTAL SIGNALS", value="0")
with col2:
    box_support = st.empty()
    box_support.metric(label="🟢 SUPPORTS", value="0")
with col3:
    box_resistance = st.empty()
    box_resistance.metric(label="🔴 RESISTANCES", value="0")

st.markdown("---")

# Scan Button Execution
if st.button("🚀 Start Scanning Now", use_container_width=True):
    if not selected_exchanges:
        st.error("Khabardar! Kam se kam ek exchange select karein.")
    else:
        results = []
        total_signals = 0
        support_count = 0
        resistance_count = 0

        # Progress bar aur status text initialization
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_steps = len(selected_exchanges) * max_coins_per_ex
        current_step = 0

        for ex_name in selected_exchanges:
            try:
                exchange_obj = EXCHANGES_MAP[ex_name]()
                markets = exchange_obj.load_markets()
                usdt_pairs = [symbol for symbol in markets if symbol.endswith('/USDT')][:max_coins_per_ex]
                
                for symbol in usdt_pairs:
                    current_step += 1
                    # Progress Percentage update
                    progress_percent = int((current_step / total_steps) * 100)
                    progress_bar.progress(min(progress_percent, 100))
                    status_text.text(f"Scanning... {progress_percent}% completed | Exchange: {ex_name} | Pair: {symbol}")

                    try:
                        bars = exchange_obj.fetch_ohlcv(symbol, timeframe=timeframe, limit=5)
                        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        
                        signal, price = analyze_candlesticks(df, tolerance_pct=tolerance)
                        if signal:
                            sig_type = "🟢 Support" if "SUPPORT" in signal else "🔴 Resistance"
                            
                            if "SUPPORT" in signal:
                                support_count += 1
                            else:
                                resistance_count += 1
                            
                            total_signals += 1

                            # Update summary boxes real-time
                            box_total.metric(label="TOTAL SIGNALS", value=str(total_signals))
                            box_support.metric(label="🟢 SUPPORTS", value=str(support_count))
                            box_resistance.metric(label="🔴 RESISTANCES", value=str(resistance_count))

                            results.append({
                                "Exchange": ex_name,
                                "Pair": symbol,
                                "Type": sig_type,
                                "Timeframe": timeframe,
                                "Price Level": price
                            })
                    except Exception:
                        continue
            except Exception as e:
                st.warning(f"{ex_name} connect karne mein error aya: {e}")

        # Completion Status
        progress_bar.progress(100)
        status_text.success("Scan Completed 100%!")

        # Results Table Display
        if results:
            st.subheader("📋 Detected Signals Result Table")
            res_df = pd.DataFrame(results)
            st.dataframe(res_df, use_container_width=True)
        else:
            st.warning("In settings par koi signal nahi mila.")
