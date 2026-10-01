import streamlit as st
import ccxt
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Crypto Multi-Exchange Scanner", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Mobile Responsive Boxes (3 Cards Layout)
st.markdown("""
    <style>
    .stMetric {
        background-color: #1e222d;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #2a2e39;
        text-align: center;
    }
    .stDataFrame {
        font-size: 13px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Multi-Exchange Crypto Scanner")

# Expanded Multi-Exchange Setup
EXCHANGES_MAP = {
    'Binance': ccxt.binance,
    'Bybit': ccxt.bybit,
    'OKX': ccxt.okx,
    'MEXC': ccxt.mexc,
    'KuCoin': ccxt.kucoin,
    'Gate.io': ccxt.gateio,
    'Bitget': ccxt.bitget,
    'BingX': ccxt.bingx
}

def analyze_candlesticks(df, tolerance_pct=0.5):
    if len(df) < 3:
        return None, None

    prev = df.iloc[-2]  # Previous Candle
    curr = df.iloc[-1]  # Current Candle

    # 1. Bullish Engulfing Support (Choti Red -> Badi Green)
    is_prev_bearish = prev['close'] < prev['open']
    is_curr_bullish = curr['close'] > curr['open']
    is_bullish_engulfing = is_prev_bearish and is_curr_bullish and (curr['close'] >= prev['open']) and (curr['open'] <= prev['close'])

    if is_bullish_engulfing:
        support_level = curr['low']
        gap = abs(curr['close'] - support_level) / support_level * 100
        if gap <= tolerance_pct:
            return "SUPPORT_BULLISH_ENGULFING", support_level

    # 2. Bearish Engulfing Resistance (Choti Green -> Badi Red)
    is_prev_bullish = prev['close'] > prev['open']
    is_curr_bearish = curr['close'] < curr['open']
    is_bearish_engulfing = is_prev_bullish and is_curr_bearish and (curr['open'] >= prev['close']) and (curr['close'] <= prev['open'])

    if is_bearish_engulfing:
        resistance_level = curr['high']
        gap = abs(resistance_level - curr['close']) / resistance_level * 100
        if gap <= tolerance_pct:
            return "RESISTANCE_BEARISH_ENGULFING", resistance_level

    return None, None

# --- UI Sidebar / Inputs ---
st.subheader("⚙️ Settings")
selected_exchanges = st.multiselect("Select Exchanges", list(EXCHANGES_MAP.keys()), default=['Binance', 'Bybit', 'OKX', 'MEXC'])
timeframe = st.selectbox("Timeframe", ['15m', '1h', '4h', '1d'], index=1)
tolerance = st.slider("Tolerance Gap (%)", 0.1, 2.0, 0.5)
coins_limit = st.slider("Coins Limit Per Exchange", 10, 100, 30)

# --- Top 3 Advanced Mobile Boxes ---
col1, col2, col3 = st.columns(3)

with col1:
    total_box = st.empty()
    total_box.metric(label="TOTAL SIGNALS", value="0")

with col2:
    support_box = st.empty()
    support_box.metric(label="🟢 SUPPORTS", value="0")

with col3:
    resistance_box = st.empty()
    resistance_box.metric(label="🔴 RESISTANCES", value="0")

st.markdown("---")

# --- Scan Logic Execution ---
if st.button("🚀 Start Multi-Exchange Scan", use_container_width=True):
    if not selected_exchanges:
        st.warning("Kam se kam ek Exchange lazmi select karein!")
    else:
        st.info("Scanning progress in background...")
        results = []
        
        total_signals = 0
        support_count = 0
        resistance_count = 0

        for ex_name in selected_exchanges:
            try:
                exchange_class = EXCHANGES_MAP[ex_name]()
                markets = exchange_class.load_markets()
                usdt_pairs = [symbol for symbol in markets if symbol.endswith('/USDT')][:coins_limit]
                
                for symbol in usdt_pairs:
                    try:
                        bars = exchange_class.fetch_ohlcv(symbol, timeframe=timeframe, limit=5)
                        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        
                        signal, price = analyze_candlesticks(df, tolerance_pct=tolerance)
                        if signal:
                            sig_type = "🟢 Support" if "SUPPORT" in signal else "🔴 Resistance"
                            
                            if "SUPPORT" in signal:
                                support_count += 1
                            else:
                                resistance_count += 1
                            
                            total_signals += 1
                            
                            # Live Boxes Update
                            total_box.metric(label="TOTAL SIGNALS", value=str(total_signals))
                            support_box.metric(label="🟢 SUPPORTS", value=str(support_count))
                            resistance_box.metric(label="🔴 RESISTANCES", value=str(resistance_count))

                            results.append({
                                "Exchange": ex_name,
                                "Pair": symbol,
                                "Type": sig_type,
                                "Timeframe": timeframe,
                                "Price Level": price,
                                "Gap %": f"{tolerance}%"
                            })
                    except Exception:
                        continue
            except Exception as e:
                st.error(f"{ex_name} load karne mein error aya: {e}")
                continue

        if results:
            res_df = pd.DataFrame(results)
            st.success("Scan mukammal ho gaya hai!")
            st.dataframe(res_df, use_container_width=True)
        else:
            st.warning("Chuni hui settings par koi signal nahi mila.")
