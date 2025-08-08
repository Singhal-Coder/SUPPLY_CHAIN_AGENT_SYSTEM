import streamlit as st
import requests
import time
import os

from dotenv import load_dotenv
import logging

from sqlalchemy import create_engine, text
from prophet import Prophet
import plotly.graph_objects as go
import pandas as pd

logging.getLogger('cmdstanpy').setLevel(logging.ERROR)

# --- Page Configuration ---
st.set_page_config(
    page_title="Supply Chain Resilience System",
    page_icon="🤖",
    layout="wide"
)
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
ANALYSIS_ENDPOINT = f"{API_BASE_URL}/run_analysis"

def render_title_and_description() -> None:
    st.title("🤖 Intelligent Supply Chain Resilience System")
    st.markdown("This dashboard runs a multi-agent analysis to identify at-risk suppliers and find related global news.")


# --- Initialize session state ---
def init_session_state():
    default_session_state = {
        'analysis_running': False,
        'analysis_done': False,
        'alerts': [],
        'api_key': None,
        'project_id': None,
        'manual_analysis_selected': False,
    }
    for key, value in default_session_state.items():
        if key not in st.session_state:
            st.session_state[key] = value

def render_mode_toggle() -> None:
    mode = st.radio(
        "Select Analysis Mode:",
        ('Latest Automated Results', 'Run New Manual Analysis'),
        horizontal=True
    )
    if mode == 'Run New Manual Analysis':
        st.session_state.manual_analysis_selected = True
    else:
        st.session_state.manual_analysis_selected = False

@st.cache_data(ttl=600) # Cache the data for 10 minutes
def fetch_latest_alerts():


    if not DATABASE_URL:
        st.error("DATABASE_URL is not set. Please configure your environment variables.")
        return pd.DataFrame()
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            df = pd.read_sql(
                text("""
                    SELECT a.*, s.latitude, s.longitude, s.risk_score, s.supplier_name
                    FROM alerts a
                    JOIN suppliers s ON a.supplier_id = s.supplier_id
                    ORDER BY a.timestamp DESC
                    LIMIT 10;
                """),
                conn
            )
            # Ensure timestamp is datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
    except Exception as e:
        st.error(f"Could not fetch alerts: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600) # Cache forecast for 1 hour
def generate_forecast_data(product_id: str):
    """
    Fetches sales data and runs Prophet to generate a forecast.
    """
    if DATABASE_URL is None: return None
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            sales_query = text("SELECT ds, y FROM sales_history WHERE product_id = :pid ORDER BY ds;")
            history = pd.read_sql(sales_query, conn, params={'pid': product_id}, parse_dates=['ds'])
        
        if len(history) < 10: return None

        model = Prophet(weekly_seasonality=True, daily_seasonality=False)
        model.fit(history)
        future = model.make_future_dataframe(periods=12, freq='W') # Forecast 12 weeks
        forecast = model.predict(future)
        merged_df = pd.merge(forecast, history, on='ds', how='left')
        return merged_df
    except Exception as e:
        st.error(f"Could not generate forecast: {e}")
        return None


def render_automatic_mode() -> None:
    st.subheader("Displaying Latest Results from 24/7 Monitoring")
    alerts_df = fetch_latest_alerts()
    if not alerts_df.empty:
        st.map(alerts_df, latitude='latitude', longitude='longitude', size='risk_score')

        st.subheader("📢 Latest Monitored Risks:")
        for _, row in alerts_df.iterrows():
            priority = row['priority']
            ts_str   = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')
            with st.expander(f"**{priority} ALERT** for **{row['supplier_name']}** (Monitored on: {ts_str})"):
                st.text_area(
                    "Alert",
                    value=row['alert_text'],
                    height=300,
                    disabled=True,
                    key=f"db_alert_{row['id']}",
                    label_visibility="collapsed",
                )
    else:
        st.info("No recent alerts found in the database. The system might be running its first analysis.")

    

def render_manual_sidebar() -> None:
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.markdown("Enter your IBM watsonx.ai credentials below.")

        # Use text_input with type="password" to obscure the keys
        api_key_input = st.text_input(
            "Watsonx API Key",
            type="password",
            value=st.session_state.api_key if st.session_state.api_key is not None else "",
        )
        project_id_input = st.text_input(
            "Watsonx Project ID",
            type="password",
            value=st.session_state.project_id if st.session_state.project_id is not None else "",
        )

        if st.button("Save Credentials"):
            if api_key_input and project_id_input:
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

def handle_analysis_execution() -> None:
    st.subheader("🔄 Trigger a New, On-Demand Analysis")
    if st.session_state.analysis_running:
        with st.spinner('Agents are analyzing... Please wait.'):
            try:
                response = requests.get(
                    ANALYSIS_ENDPOINT,
                    params={
                        'api_key': st.session_state.api_key,
                        'project_id': st.session_state.project_id,
                    },
                )
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

def render_manual_controls_and_results(credentials_ready: bool) -> None:
    run_btn = st.button(
        '▶️ Run Full Analysis',
        disabled=st.session_state.analysis_running or not credentials_ready,
    )
    if not st.session_state.analysis_running and not st.session_state.analysis_done:
        st.info("Click the button above to start the analysis.")

    if run_btn:
        st.session_state.analysis_running = True
        st.rerun()

    if st.session_state.analysis_done:
        if st.session_state.alerts:
            st.subheader("Analysis Results:")
            for alert in st.session_state.alerts:
                st.text_area("Alert", value=alert, height=250, disabled=True)
        else:
            st.info("No alerts to display.")

def render_manual_mode() -> None:
    render_manual_sidebar()
    handle_analysis_execution()
    credentials_ready = (
        st.session_state.api_key is not None and st.session_state.project_id is not None
    )
    render_manual_controls_and_results(credentials_ready)

def render_forecast_chart() -> None:
    # --- Interactive Forecast Chart (Always Visible) ---
    st.markdown("---")
    st.subheader("📈 Interactive Demand Forecast")
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        query = text("SELECT product_id, product_name FROM products")
        products = pd.read_sql(query, conn)
        product_options = {row['product_name']: row['product_id'] for _, row in products.iterrows()}

    product_names = ["Select a Product"] + list(product_options.keys())
    selected_product_name = st.selectbox("Select a Product to Forecast:", options=product_names)
    if selected_product_name == "Select a Product":
        selected_product_name = None

    if selected_product_name:
        with st.spinner(f"Generating forecast for {selected_product_name}..."):
            forecast_df = generate_forecast_data(product_options[selected_product_name])

        if forecast_df is not None:
            # Create a Plotly figure
            fig = go.Figure()
            # Add confidence interval shading
            fig.add_trace(go.Scatter(
                x=forecast_df['ds'], y=forecast_df['yhat_upper'], fill=None, mode='lines', 
                line=dict(color='rgba(0,176,246,0.2)'), name='Confidence Upper Bound'
            ))
            fig.add_trace(go.Scatter(
                x=forecast_df['ds'], y=forecast_df['yhat_lower'], fill='tonexty', mode='lines', 
                line=dict(color='rgba(0,176,246,0.2)'), name='Confidence Lower Bound'
            ))
            # Add historical data points
            fig.add_trace(go.Scatter(x=forecast_df['ds'], y=forecast_df['y'], mode='markers', name='Historical Sales', marker=dict(color='white')))
            # Add the main forecast line
            fig.add_trace(go.Scatter(x=forecast_df['ds'], y=forecast_df['yhat'], mode='lines', name='Forecast', line=dict(color='#00b0f0', width=3)))

            fig.update_layout(
                title=f'Sales Forecast for {selected_product_name}',
                xaxis_title='Date', yaxis_title='Weekly Units Sold',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Could not generate forecast for {selected_product_name}.")

def main() -> None:
    init_session_state()
    render_title_and_description()
    render_mode_toggle()
    if not st.session_state.manual_analysis_selected:
        render_automatic_mode()
    else:
        render_manual_mode()
        render_forecast_chart()

if __name__ == "__main__":
    main()
