import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"
st.set_page_config(page_title="Incident History", page_icon="📜", layout="wide")
st.title("Incident History")

try:
    incidents = requests.get(f"{API_URL}/incidents").json()
    if incidents:
        df = pd.DataFrame(incidents)
        st.dataframe(
            df[['incident_id', 'started_at', 'failure_type', 'diagnosis_source', 'recommended_action', 'risk_level', 'final_status', 'recovery_attempts']], 
            use_container_width=True
        )
    else:
        st.info("No incidents recorded yet.")
except Exception as e:
    st.error(f"Error loading incidents: {e}")
