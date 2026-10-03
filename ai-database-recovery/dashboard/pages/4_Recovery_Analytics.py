import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://localhost:8000"
st.set_page_config(page_title="Recovery Analytics", page_icon="📈", layout="wide")
st.title("Recovery Analytics")

try:
    incidents = requests.get(f"{API_URL}/incidents").json()
    if incidents:
        df = pd.DataFrame(incidents)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Incidents by Failure Type")
            fig1 = px.pie(df, names='failure_type', title='Failure Types')
            st.plotly_chart(fig1, use_container_width=True)
            
        with col2:
            st.subheader("Resolution Status")
            fig2 = px.pie(df, names='final_status', title='Final Status')
            st.plotly_chart(fig2, use_container_width=True)
            
        st.subheader("LLM Latency Distribution")
        df_llm = df[df['llm_latency_seconds'].notnull()]
        if not df_llm.empty:
            fig3 = px.box(df_llm, y='llm_latency_seconds', x='diagnosis_source', title='Diagnosis Latency by Source')
            st.plotly_chart(fig3, use_container_width=True)
            
    else:
        st.info("Not enough data to display analytics.")
except Exception as e:
    st.error(f"Error loading analytics: {e}")
