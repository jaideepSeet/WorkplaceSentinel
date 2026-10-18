import time
import json
import os
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Workplace Safety Sentinel Dashboard", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .alert-banner { padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 22px; margin-bottom: 20px; }
    .danger { background-color: #da3633; color: white; }
    .safe { background-color: #238636; color: white; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🛡️ Sentinel Hub")
    st.markdown("**Track A:** Workplace Safety")
    st.markdown("**Zone:** `SECTOR_B_HAZARD`")
    st.markdown("---")
    auto_refresh = st.checkbox("Live Auto-Refresh", value=True)
    refresh_rate = st.slider("Refresh rate (s)", 1, 5, 2)

st.title("🛡️ Workplace Safety Sentinel Command Center")
st.markdown("Real-time hazard zone intrusion detection and compliance monitoring.")

log_file = "safety_incidents.jsonl"

def load_incidents():
    if not os.path.exists(log_file):
        return []
    data = []
    with open(log_file, "r") as f:
        for line in f:
            if line.strip():
                try:
                    data.append(json.loads(line.strip()))
                except:
                    pass
    return data

placeholder = st.empty()

while True:
    incidents = load_incidents()
    
    with placeholder.container():
        if incidents:
            latest = incidents[-1]
            st.markdown('<div class="alert-banner danger">🚨 ACTIVE SAFETY VIOLATION DETECTED IN RESTRICTED ZONE!</div>', unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Violations Logged", len(incidents))
            c2.metric("Latest Worker ID", f"Worker #{latest['worker_id']}")
            c3.metric("Incident Type", latest['event'])
            c4.metric("Timestamp", latest['timestamp'][11:19])
            
            st.markdown("---")
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.subheader("📊 Violation Timeline")
                df = pd.DataFrame(incidents)
                if not df.empty:
                    st.line_chart(df.index)
            with col_b:
                st.subheader("📝 Incident Audit Log")
                for inc in reversed(incidents[-5:]):
                    st.markdown(f"> **{inc['event']}** (Worker #{inc['worker_id']}) at `{inc['timestamp'][11:19]}`")
        else:
            st.markdown('<div class="alert-banner safe">🟢 SITE SECURE: NO HAZARD INTRUSIONS DETECTED</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            col1.metric("Total Violations Logged", 0)
            col2.metric("Zone Status", "Clear")
            st.info("Run your `sentinel_monitor.py` script with a video to generate live incident data.")

    if not auto_refresh:
        break
    time.sleep(refresh_rate)
    st.rerun()
