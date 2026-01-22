import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# --- 1. Page Config & CSS ---
st.set_page_config(page_title="Real-time Price Ladder", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0b0e11; color: #eaecef; }
    .price-box {
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .buy-level { background-color: rgba(38, 166, 154, 0.2); border: 1px solid #26a69a; }
    .current-level { background-color: rgba(255, 255, 255, 0.1); border: 2px solid #f0b90b; }
</style>
""", unsafe_allow_html=True)

# --- 2. Data Functions ---
def get_bitkub_price(symbol):
    try:
        url = "https://api.bitkub.com/api/market/ticker"
        data = requests.get(url).json()
        ticker = data.get(f"THB_{symbol}")
        return float(ticker['last']) if ticker else 0.0
    except: return 0.0

# --- 3. Sidebar Setup ---
with st.sidebar:
    st.header("⚙️ Trading Setup")
    coin_list = ['BTC', 'ETH', 'KUB', 'XRP', 'DOGE', 'SOL']
    selected_coin = st.selectbox("เลือกเหรียญ", coin_list)
    entry_price = st.number_input("ราคาที่คุณซื้อ (Entry Price)", value=0.0, format="%.2f")
    step_size = st.number_input("ระดับราคาห่างกันช่องละ (Step)", value=10.0)
    if st.button("🔄 Refresh"): st.rerun()

# --- 4. Main Logic ---
live_price = get_bitkub_price(selected_coin)

if live_price > 0:
    # ส่วนหัว: แสดงราคาเปรียบเทียบ
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="price-box buy-level">Entry: ฿{entry_price:,.2f}</div>', unsafe_allow_html=True)
    with c2:
        diff = live_price - entry_price
        color = "#2ebd85" if diff >= 0 else "#f6465d"
        st.markdown(f'<div class="price-box" style="color:{color}; border: 1px solid {color}">Gap: ฿{diff:,.2f}</div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="price-box current-level">Live: ฿{live_price:,.2f}</div>', unsafe_allow_html=True)

    st.divider()

    # --- 5. Price Ladder (ตารางระดับราคาแบบเรียลไทม์) ---
    st.subheader(f"📊 {selected_coin} Price Ladder (Real-time Levels)")
    
    # สร้างช่วงระดับราคารอบๆ ราคาปัจจุบัน
    num_levels = 10
    levels = []
    # สร้างระดับราคาขึ้นและลงจากราคาปัจจุบัน
    for i in range(num_levels, -num_levels - 1, -1):
        target_p = live_price + (i * step_size)
        pnl_at_level = ((target_p - entry_price) / entry_price * 100) if entry_price > 0 else 0
        
        # กำหนดสถานะ
        status = ""
        if abs(target_p - live_price) < step_size: status = "⚡ CURRENT"
        elif abs(target_p - entry_price) < step_size: status = "🚩 ENTRY"

        levels.append({
            "Status": status,
            "Price Level": f"฿{target_p:,.2f}",
            "Diff from Entry": f"{target_p - entry_price:,.2f}",
            "ROE (%)": f"{pnl_at_level:+.2f}%"
        })

    df_ladder = pd.DataFrame(levels)

    # ฟังก์ชันช่วยแต่งสีในตาราง
    def color_pnl(val):
        color = '#2ebd85' if '+' in str(val) else '#f6465d'
        if '0.00%' in str(val): color = '#eaecef'
        return f'color: {color}'

    # แสดงตารางแบบจัดเต็ม
    st.dataframe(
        df_ladder.style.applymap(color_pnl, subset=['ROE (%)']),
        use_container_width=True,
        hide_index=True
    )

    # --- 6. กราฟเปรียบเทียบแนวโน้ม (Simple Area Chart) ---
    st.divider()
    st.write("📈 ความห่างจากราคาซื้อ (Visual Gap Tracking)")
    # สมมติประวัติราคาเพื่อวาดกราฟ (ในที่นี้ใช้เส้นตรงเปรียบเทียบ)
    fig = go.Figure()
    fig.add_hline(y=entry_price, line_dash="dash", line_color="#f0b90b", annotation_text="ENTRY")
    fig.add_trace(go.Indicator(
        mode = "gauge+number",
        value = live_price,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Current Price vs Entry"},
        gauge = {
            'axis': {'range': [entry_price * 0.8, entry_price * 1.2]},
            'bar': {'color': "#2ebd85" if live_price >= entry_price else "#f6465d"},
            'steps': [{'range': [0, entry_price], 'color': "rgba(246, 70, 93, 0.1)"}],
            'threshold': {'line': {'color': "yellow", 'width': 4}, 'thickness': 0.75, 'value': entry_price}
        }
    ))
    fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("กรุณาเลือกเหรียญและรอการเชื่อมต่อ API...")
    
