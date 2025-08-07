import streamlit as st
import requests
import time
import os
from dotenv import load_dotenv

# --- Page Configuration ---
st.set_page_config(
    page_title="Supply Chain Resilience System",
    page_icon="🤖",
    layout="wide"
)
load_dotenv()
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
ANALYSIS_ENDPOINT = f"{API_BASE_URL}/run_analysis"
with st.sidebar:
    st.header("⚙️ Configuration")
    st.markdown("Enter your IBM watsonx.ai credentials below.")
    
    # Use text_input with type="password" to obscure the keys
    api_key_input = st.text_input("Watsonx API Key", type="password")
    project_id_input = st.text_input("Watsonx Project ID", type="password")
    
    if st.button("Save Credentials"):
        if api_key_input and project_id_input:
            # st.session_state is Streamlit's way to store variables across reruns
            st.session_state['api_key'] = api_key_input
            st.session_state['project_id'] = project_id_input
            st.success("Credentials saved successfully!")
        else:
            st.error("Please enter both an API Key and a Project ID.")

    st.markdown("---")
    st.markdown("Don't have an API Key?")
    st.markdown("1. [Sign up for IBM Cloud](https://cloud.ibm.com/registration)")
    st.markdown("2. [Follow this guide to create an API key](https://cloud.ibm.com/docs/account?topic=account-userapikey&interface=ui)")
    st.markdown("3. [Find your Project ID in watsonx.ai](https://dataplatform.cloud.ibm.com/wx/home)")


st.title("🤖 Intelligent Supply Chain Resilience System")
st.markdown("This dashboard runs a multi-agent analysis to identify at-risk suppliers and find related global news.")


# --- Initialize session state ---
if 'analysis_running' not in st.session_state:
    st.session_state.analysis_running = False

if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False

if 'alerts' not in st.session_state:
    st.session_state.alerts = []

# --- If analysis is running: do the work ---
if st.session_state.analysis_running:
    with st.spinner('Agents are analyzing... Please wait.'):
        try:
            response = requests.get(ANALYSIS_ENDPOINT, params={
                'api_key': st.session_state['api_key'],
                'project_id': st.session_state['project_id']
            })
            response.raise_for_status()
            results = response.json()
            st.session_state.alerts = results.get("alerts", [])
            st.success('Analysis Complete!')
            time.sleep(1)
        except requests.exceptions.RequestException as e:
            st.error(f"Error: Could not connect to the API server. Details: {e}")
            st.session_state.alerts = []
    st.session_state.analysis_running = False
    st.session_state.analysis_done = True
    st.rerun()

credentials_ready = 'api_key' in st.session_state and 'project_id' in st.session_state

# --- Show main UI ---
run_btn = st.button(
        '▶️ Run Full Analysis',
        disabled=st.session_state.analysis_running or not credentials_ready
    )
if not st.session_state.analysis_running and not st.session_state.analysis_done:
    st.info("Click the button above to start the analysis.")

# --- On click: flag running and refresh ---
if run_btn:
    st.session_state.analysis_running = True
    st.rerun()

# --- Once done: show results ---
if st.session_state.analysis_done:
    if st.session_state.alerts:
        st.subheader("Analysis Results:")
        for alert in st.session_state.alerts:
            st.text_area("Alert", value=alert, height=250, disabled=True)
    else:
        st.info("No alerts to display.")
