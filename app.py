import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# --- ตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Pro Crypto Terminal", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS เพื่อความสวยงาม ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #d1d5db; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: 0px 4px 6px rgba(0,0,0,0.1); }
    .buy-btn { background-color: #28a745 !important; color: white !important; }
    .sell-btn { background-color: #dc3545 !important; color: white !important; }
    .status-card { padding: 20px; border-radius: 15px; border-left: 5px solid #007bff; background: #ffffff; }
</style>
""", unsafe_allow_html=True)

# --- Functions (เหมือนเดิมแต่ปรับ Error Handling) ---
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

# --- Initialize Session State ---
if 'history' not in st.session_state: st.session_state.history = []
if 'active_trade' not in st.session_state: st.session_state.active_trade = None

# --- Header ---
c_title, c_status = st.columns([3, 1])
with c_title:
    st.title("⚡ Pro Trading Terminal")
with c_status:
    st.write("") # Spacer
    if st.button('🔄 Refresh Market Data'): st.rerun()

# --- Sidebar ---
with st.sidebar:
    st.header("🎮 Control Panel")
    coin_list = ['BTC', 'ETH', 'KUB', 'XRP', 'DOGE', 'SOL', 'BNB']
    selected_coin = st.selectbox("เลือกสินทรัพย์ (Asset)", coin_list)
    
    with st.container():
        st.subheader("💰 Portfolio Setup")
        balance = st.number_input("เงินต้น (Margin) ฿", value=1000.0, step=100.0)
        leverage = st.slider("Leverage (x)", 1, 50, 1)

# --- ข้อมูลตลาด ---
live_price = get_bitkub_price(selected_coin)
df_candles = get_candles(selected_coin)

# --- Main Layout ---
col_chart, col_trade = st.columns([2.5, 1])

with col_chart:
    # แสดงกราฟแท่งเทียน
    if not df_candles.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df_candles['time'], open=df_candles['o'], high=df_candles['h'],
            low=df_candles['l'], close=df_candles['c'],
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
        )])
        fig.update_layout(
            height=550, margin=dict(l=0, r=0, t=0, b=0),
            template="plotly_white", xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)

with col_trade:
    # แผงซื้อขาย
    st.subheader("🚀 Trade Action")
    with st.container():
        st.markdown(f"**Asset:** {selected_coin}/THB")
        st.markdown(f"**Live Price:** <span style='color:#007bff; font-size:20px; font-weight:bold;'>{live_price:,.2f}</span>", unsafe_allow_html=True)
        
        st.divider()
        
        if st.session_state.active_trade is None:
            st.info("ยังไม่มีสถานะที่เปิดอยู่")
            if st.button("🟢 OPEN LONG POSITION", key="buy_btn", help="คลิกเพื่อซื้อ"):
                st.session_state.active_trade = {
                    'symbol': selected_coin, 'entry': live_price, 
                    'margin': balance, 'lev': leverage, 'time': datetime.now()
                }
                st.rerun()
        else:
            trade = st.session_state.active_trade
            # คำนวณ P/L สุทธิ (หัก Fee 0.25% x 2)
            pos_size = trade['margin'] * trade['lev']
            qty = (pos_size * (1 - 0.0025)) / trade['entry']
            current_val = qty * live_price
            net_pnl = (current_val * (1 - 0.0025)) - trade['margin']
            pnl_pct = (net_pnl / trade['margin']) * 100
            
            st.warning(f"ถือครอง: {trade['symbol']} @ {trade['entry']:,.2f}")
            color = "green" if net_pnl >= 0 else "red"
            st.markdown(f"### P/L: <span style='color:{color}'>฿{net_pnl:,.2f} ({pnl_pct:.2f}%)</span>", unsafe_allow_html=True)
            
            if st.button("🔴 CLOSE & TAKE PROFIT", key="sell_btn"):
                st.session_state.history.append({
                    'Time': datetime.now().strftime("%H:%M:%S"),
                    'Symbol': trade['symbol'],
                    'Entry': f"{trade['entry']:,.2f}",
                    'Exit': f"{live_price:,.2f}",
                    'P/L (Net)': f"{net_pnl:,.2f}"
                })
                st.session_state.active_trade = None
                st.balloons()
                st.rerun()

# --- ประวัติการเทรดแบบสวยงาม ---
st.divider()
st.subheader("📜 Trading Journal")
if st.session_state.history:
    df_history = pd.DataFrame(st.session_state.history)
    st.dataframe(df_history, use_container_width=True, hide_index=True)
else:
    st.write("เริ่มเทรดเพื่อดูประวัติของคุณตรงนี้")

