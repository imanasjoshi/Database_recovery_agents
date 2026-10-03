import streamlit as st
import requests
import pandas as pd
import time

API_URL = "http://localhost:8000"

st.set_page_config(page_title="System Overview", page_icon="📊", layout="wide")

st.title("System Overview")

def get_status():
    try:
        return requests.get(f"{API_URL}/status").json()
    except:
        return None

status_data = get_status()

if status_data:
    cols = st.columns(4)
    status_color = "green" if status_data['current_status'] == "HEALTHY" else ("red" if status_data['current_status'] in ["FAILED", "ESCALATED"] else "orange")
    
    cols[0].metric("System Status", status_data['current_status'])
    cols[1].metric("Total Incidents", status_data['failure_count'])
    cols[2].metric("Successful Recoveries", status_data['successful_recoveries'])
    cols[3].metric("Escalated/Failed", status_data['failed_recoveries'])
    
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Monitor Control")
        c1, c2 = st.columns(2)
        if c1.button("Start Monitoring"):
            requests.post(f"{API_URL}/monitor/start")
            st.success("Started")
            time.sleep(1)
            st.rerun()
        if c2.button("Stop Monitoring"):
            requests.post(f"{API_URL}/monitor/stop")
            st.warning("Stopped")
            time.sleep(1)
            st.rerun()
            
    with col2:
        st.subheader("Simulate Incident")
        options = ["connection_timeout", "missing_table", "database_locked", "permission_error"]
        selected_failure = st.selectbox("Failure Type", options)
        if st.button("Trigger Incident"):
            res = requests.post(f"{API_URL}/incidents/simulate", json={"failure_type": selected_failure})
            st.toast(res.json().get("message", "Simulated"))
            time.sleep(1)
            st.rerun()
            
    # Approvals
    if status_data['current_status'] == "AWAITING_APPROVAL":
        st.error(f"High-Risk Recovery Suggested for Incident: {status_data['current_incident_id']}")
        a1, a2 = st.columns(2)
        if a1.button("Approve Recovery"):
            requests.post(f"{API_URL}/recovery/{status_data['current_incident_id']}/approve")
            st.rerun()
        if a2.button("Reject / Escalate"):
            requests.post(f"{API_URL}/recovery/{status_data['current_incident_id']}/reject")
            st.rerun()

    # Auto refresh logic
    if status_data['current_status'] not in ["HEALTHY", "ESCALATED"]:
        time.sleep(2)
        st.rerun()
else:
    st.error("Cannot connect to API backend. Is it running?")
