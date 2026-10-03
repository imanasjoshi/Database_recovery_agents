import streamlit as st

st.set_page_config(
    page_title="DB Recovery Platform",
    page_icon="🛡️",
    layout="wide"
)

st.title("AI-Powered Database Reliability Platform")
st.sidebar.success("Select a page above.")

st.markdown("""
Welcome to the Multi-Agent Database Recovery Platform!

Use the sidebar to navigate through the dashboard:
- **System Overview:** View current state and simulate incidents.
- **Incident History:** Browse past incidents.
- **Agent Activity:** View the internal message bus.
- **Recovery Analytics:** View metrics and charts.
""")
