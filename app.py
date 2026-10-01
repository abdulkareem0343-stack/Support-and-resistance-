import streamlit as st
import ccxt
import pandas as pd

# Page Setup - Optimized for Mobile
st.set_page_config(page_title="Crypto Multi-Exchange Scanner", layout="wide", initial_sidebar_state="collapsed")

# Mobile Responsive Advanced Box Styling
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #1e222d 0%, #2a2e39 100%);
        border: 1px solid #363c4e;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-label {
        font-size: 12px;
        color: #8f9cae;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 22px;
        font-weight: bold;
        color: #ffffff;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Multi-Exchange Crypto Scanner")

# Fixed Exchanges Map
EXCHANGES_MAP = {
    'Binance': ccxt.binance,
    'Bybit': ccxt.bybit,
    'OKX': ccxt.okx,
    'MEXC': ccxt.mexc,
    'KuCoin': ccxt.kucoin,
    'Gate.io': ccxt.gate,
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

# Default Coins Limit Set to 500
max_coins_per_ex = st.number_input("Total Top Coins Limit (Per Exchange)", min_value=10, max_value=1000, value=500, step=50)

st.markdown("---")

# Mobile Advanced Summary Boxes Containers
col1, col2, col3 = st.columns(3)

with col1:
    box_total = st.empty()
    box_total.markdown("""
        <div class="metric-card">
            <div class="metric-label">TOTAL SIGNALS</div>
            <div class="metric-value">0</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    box_support = st.empty()
    box_support.markdown("""
        <div class="metric-card">
            <div class="metric-label">🟢 SUPPORTS</div>
            <div class="metric-value" style="color: #00e676;">0</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    box_resistance = st.empty()
    box_resistance.markdown("""
        <div class="metric-card">
            <div class="metric-label">🔴 RESISTANCES</div>
            <div class="metric-value" style="color: #ff5252;">0</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Scan Execution
if st.button("🚀 Start Scanning Now", use_container_width=True):
    if not selected_exchanges:
        st.error("Khabardar! Kam se kam ek exchange select karein.")
    else:
        results = []
        total_signals = 0
        support_count = 0
        resistance_count = 0

        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_steps = len(selected_exchanges) * max_coins_per_ex
        current_step = 0

        for ex_name in selected_exchanges:
            try:
                exchange_obj = EXCHANGES_MAP[ex_name]()
                markets = exchange_obj.load_markets()
                
                # Fetch Top Volume USDT Pairs (Top 500 Coins)
                usdt_pairs = [symbol for symbol in markets if symbol.endswith('/USDT')][:max_coins_per_ex]
                
                for symbol in usdt_pairs:
                    current_step += 1
                    progress_percent = int((current_step / total_steps) * 100)
                    progress_bar.progress(min(progress_percent, 100))
                    status_text.text(f"Scanning Top Coins... {progress_percent}% | {ex_name} | Pair: {symbol}")

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

                            # Update Advanced Mobile Cards Real-time
                            box_total.markdown(f"""
                                <div class="metric-card">
                                    <div class="metric-label">TOTAL SIGNALS</div>
                                    <div class="metric-value">{total_signals}</div>
                                </div>
                            """, unsafe_allow_html=True)

                            box_support.markdown(f"""
                                <div class="metric-card">
                                    <div class="metric-label">🟢 SUPPORTS</div>
                                    <div class="metric-value" style="color: #00e676;">{support_count}</div>
                                </div>
                            """, unsafe_allow_html=True)

                            box_resistance.markdown(f"""
                                <div class="metric-card">
                                    <div class="metric-label">🔴 RESISTANCES</div>
                                    <div class="metric-value" style="color: #ff5252;">{resistance_count}</div>
                                </div>
                            """, unsafe_allow_html=True)

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

        progress_bar.progress(100)
        status_text.success("Scan Completed 100%!")

        if results:
            st.subheader("📋 Detected Signals Result Table")
            res_df = pd.DataFrame(results)
            st.dataframe(res_df, use_container_width=True)
        else:
            st.warning("In settings par koi signal nahi mila.")
