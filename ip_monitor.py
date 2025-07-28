import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
import time

st.set_page_config(page_title="IP Мониторинг", page_icon="🌐")
st.title("🌐 Мониторинг внешнего IP-адреса")

LOG_FILE = "ip_log.csv"

check_interval = st.number_input("Интервал проверки (секунды)", min_value=10, max_value=3600, value=60, step=10)

if "last_ip" not in st.session_state:
    st.session_state.last_ip = None
if "monitoring" not in st.session_state:
    st.session_state.monitoring = False
if "last_check" not in st.session_state:
    st.session_state.last_check = 0

def get_current_ip():
    try:
        response = requests.get("https://api.ipify.org")
        return response.text.strip()
    except:
        return None

def log_ip(ip, timestamp):
    header = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a") as f:
        if header:
            f.write("timestamp,ip\n")
        f.write(f"{timestamp},{ip}\n")

def load_log():
    if os.path.exists(LOG_FILE):
        return pd.read_csv(LOG_FILE)
    else:
        return pd.DataFrame(columns=["timestamp", "ip"])

def clear_log():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

def play_beep():
    beep_js = """
    <script>
    const context = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = context.createOscillator();
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(800, context.currentTime);
    oscillator.connect(context.destination);
    oscillator.start();
    setTimeout(() => oscillator.stop(), 300);
    </script>
    """
    st.markdown(beep_js, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if not st.session_state.monitoring:
        if st.button("▶️ Старт мониторинга"):
            st.session_state.monitoring = True
            st.success("Мониторинг запущен!")
    else:
        if st.button("⏹️ Стоп мониторинга"):
            st.session_state.monitoring = False
            st.success("Мониторинг остановлен.")

with col2:
    if st.button("🗑️ Очистить лог"):
        clear_log()
        st.success("Лог очищен")

with col3:
    if st.button("🔄 Обновить вручную"):
        st.experimental_rerun()

current_time = time.time()
if st.session_state.monitoring and (current_time - st.session_state.last_check >= check_interval):
    ip = get_current_ip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ip:
        if ip != st.session_state.last_ip:
            log_ip(ip, now)
            st.session_state.last_ip = ip
            play_beep()
            st.warning(f"🔄 IP изменился: {ip} ({now})")
        else:
            st.info(f"✅ IP не изменился: {ip} ({now})")
    else:
        st.error("⚠️ Не удалось получить IP")
    st.session_state.last_check = current_time

log_df = load_log()
if not log_df.empty:
    log_df["timestamp"] = pd.to_datetime(log_df["timestamp"])
    ip_counts = log_df.groupby(["timestamp", "ip"]).size().unstack(fill_value=0)

    st.subheader("📈 История изменений IP (график)")
    st.line_chart(ip_counts)

    st.subheader("📋 История IP-адресов (таблица)")
    st.dataframe(log_df.sort_values("timestamp", ascending=False), use_container_width=True)

