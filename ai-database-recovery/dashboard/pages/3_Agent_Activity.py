import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"
st.set_page_config(page_title="Agent Activity", page_icon="🤖", layout="wide")
st.title("Agent Message Bus")

try:
    messages = requests.get(f"{API_URL}/messages").json()
    if messages:
        df = pd.DataFrame(messages)
        st.dataframe(
            df[['timestamp', 'correlation_id', 'sender', 'receiver', 'message_type', 'data']],
            use_container_width=True
        )
    else:
        st.info("No messages recorded yet.")
except Exception as e:
    st.error(f"Error loading messages: {e}")
