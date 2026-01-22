import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# --- 1. Page Configuration ---
st.set_page_config(page_title="Professional Trading Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- 2. Custom CSS for High-End UI ---
st.markdown("""
<style>
    /* Dark Theme Setup */
    .stApp { background-color: #0b0e11; color: #eaecef; }
    
    /* Stats Cards */
    .metric-card {
        background-color: #1e2329;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #363c4e;
        text-align: center;
    }
    
    /* Control Panel Card */
    .control-panel {
        background-color: #1e2329;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #474d57;
    }

    /* Professional Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        font-weight: bold;
        border: none;
    }
    .buy-btn button { background-color: #2ebd85 !important; color: white !important; }
    .sell-btn button { background-color: #f6465d !important; color: white !important; }
    
    /* Hide Streamlit elements for clean look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. Helper Functions ---
def get_bitkub_price(symbol):
    try:
        url = "https://api.bitkub.com/api/market/ticker"
        data = requests.get(url).json()
        return float(data[f"THB_{symbol}"]['last'])
    except: return 0.0

def get_candles(symbol):
    try:
        url = f"https://api.bitkub.com/api/market/candles?symbol=THB_{symbol}&resolution=60"
        data = requests.get(url).json()
        df = pd.DataFrame(data['result'], columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        df['time'] = pd.to_datetime(df['ts'], unit='s')
        return df
    except: return pd.DataFrame()

# --- 4. Session State Management ---
if 'history' not in st.session_state: st.session_state.history = []
if 'active_trade' not in st.session_state: st.session_state.active_trade = None

# --- 5. TOP BAR: Market Overview ---
coin_list = ['BTC', 'ETH', 'KUB', 'XRP', 'DOGE', 'SOL']
selected_coin = st.sidebar.selectbox("เลือกเหรียญ", coin_list)
live_price = get_bitkub_price(selected_coin)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown(f"## {selected_coin}/THB")
with col_m2:
    st.metric("Last Price", f"฿{live_price:,.2f}")
with col_m3:
    st.metric("24h Status", "Market Open", delta="Online")
with col_m4:
    if st.button("🔄 Refresh"): st.rerun()

st.divider()

# --- 6. MAIN CONTENT: Chart & Order Panel ---
col_chart, col_order = st.columns([3, 1])

with col_chart:
    df_candles = get_candles(selected_coin)
    if not df_candles.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df_candles['time'], open=df_candles['o'], high=df_candles['h'],
            low=df_candles['l'], close=df_candles['c'],
            increasing_line_color='#2ebd85', decreasing_line_color='#f6465d'
        )])
        fig.update_layout(
            template="plotly_dark", height=600, margin=dict(l=0, r=0, t=0, b=0),
            xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

with col_order:
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    st.subheader("Place Order")
    
    margin = st.number_input("Margin (THB)", value=1000.0)
    leverage = st.slider("Leverage", 1, 50, 10)
    
    st.write("---")
    
    if st.session_state.active_trade is None:
        st.write(f"Est. Quantity: **{(margin*leverage/live_price):.6f}**")
        st.markdown('<div class="buy-btn">', unsafe_allow_html=True)
        if st.button("BUY / LONG"):
            st.session_state.active_trade = {'symbol': selected_coin, 'entry': live_price, 'margin': margin, 'lev': leverage, 'time': datetime.now()}
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        trade = st.session_state.active_trade
        # Calculate P/L
        pos_size = trade['margin'] * trade['lev']
        qty = (pos_size * (1-0.0025)) / trade['entry']
        net_pnl = (qty * live_price * (1-0.0025)) - trade['margin']
        
        st.info(f"Entry: {trade['entry']:,.2f}")
        st.markdown(f"### P/L: {'฿{:,.2f}'.format(net_pnl)}")
        
        st.markdown('<div class="sell-btn">', unsafe_allow_html=True)
        if st.button("CLOSE POSITION"):
            st.session_state.history.append({'Time': datetime.now().strftime("%H:%M"), 'Coin': trade['symbol'], 'Result': f"{net_pnl:,.2f}"})
            st.session_state.active_trade = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 7. BOTTOM: History ---
st.subheader("📜 Trading History")
if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
else:
    st.caption("No history available yet.")
