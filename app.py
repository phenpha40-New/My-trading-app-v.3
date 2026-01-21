import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- ฟังก์ชันส่ง Email ---
def send_email_alert(sender_email, app_password, receiver_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False

# --- UI ใน Sidebar ---
with st.sidebar:
    st.header("📧 Email Notification")
    sender = st.text_input("Gmail ของคุณ (Sender)")
    pwd = st.text_input("App Password (16 หลัก)", type="password")
    receiver = st.text_input("ส่งเมลไปที่ (Receiver)")
    send_on_close = st.checkbox("ส่งสรุปกำไรเข้าเมลเมื่อปิดออเดอร์")

# --- ตอนกดปิดสถานะ (Action) ---
if st.button("🔴 CLOSE POSITION"):
    # ... (โค้ดคำนวณ net_pnl เดิม) ...
    
    summary = f"""
    สรุปผลการเทรด: {trade['symbol']}
    ราคาเข้า: {trade['entry']:,.2f}
    ราคาออก: {live_price:,.2f}
    กำไรสุทธิ: {net_pnl:,.2f} THB
    วันที่: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    if send_on_close and sender and pwd and receiver:
        success = send_email_alert(sender, pwd, receiver, f"Trading Report: {trade['symbol']}", summary)
        if success:
            st.success("ส่งสรุปกำไรเข้า Email เรียบร้อย!")
