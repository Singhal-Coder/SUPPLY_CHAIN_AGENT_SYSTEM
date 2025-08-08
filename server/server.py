# server.py

from dotenv import load_dotenv
import os

from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from datetime import datetime, timezone

from .main_orchestrator import run_supply_chain_analysis
from .utils.db import get_db_engine

load_dotenv()

WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")

# Create a FastAPI application instance
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Supply Chain Resilience System API is running."}

@app.get("/run_analysis")
def run_analysis_endpoint(api_key: str, project_id: str):
    """
    This endpoint triggers the analysis using the provided credentials.
    """
    if not api_key or not project_id:
        raise HTTPException(status_code=400, detail="API key and Project ID are required.")
    
    alerts = run_supply_chain_analysis(user_api_key=api_key, user_project_id=project_id)
    return {"alerts": alerts}

@app.get("/run_scheduled_analysis")
def run_scheduled_analysis():
    """
    Runs the main analysis and saves the generated alerts to the database.
    """
    print("--- Starting Scheduled Analysis ---")
    
    alerts = run_supply_chain_analysis(WATSONX_API_KEY, WATSONX_PROJECT_ID)
    
    if not alerts or "No high-risk suppliers found" in alerts[0]:
        print("No new alerts to save.")
        print("--- Scheduled Analysis Complete ---")
        return

    # 2. Connect to the database
    try:
        engine = get_db_engine()
        with engine.connect() as connection:
            with connection.begin():
                print(f"Saving {len(alerts)} new alerts to the database...")
                # 3. Insert each new alert into the 'alerts' table
                for alert_text in alerts:
                    # Extract priority for the database record
                    priority = "UNKNOWN"
                    if "CRITICAL" in alert_text: priority = "CRITICAL"
                    elif "HIGH" in alert_text: priority = "HIGH"
                    elif "MEDIUM" in alert_text: priority = "MEDIUM"
                    elif "LOW" in alert_text: priority = "LOW"
                    
                    supplier_name_start = alert_text.find("FOR: ") + 5
                    supplier_name_end = alert_text.find("\n", supplier_name_start)
                    supplier_name = alert_text[supplier_name_start:supplier_name_end].strip()

                    stmt = text("""
                        INSERT INTO alerts (timestamp, supplier_name, priority, alert_text)
                        VALUES (:ts, :name, :prio, :text)
                    """)
                    connection.execute(stmt, {
                        "ts": datetime.now(timezone.utc),
                        "name": supplier_name,
                        "prio": priority,
                        "text": alert_text
                    })
                print("All alerts saved successfully.")

    except Exception as e:
        print(f"An error occurred while saving alerts to the database: {e}")
        
    print("--- Scheduled Analysis Complete ---")
