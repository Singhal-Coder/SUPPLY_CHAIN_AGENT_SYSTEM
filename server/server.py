# server.py

from fastapi import FastAPI, HTTPException
from main_orchestrator import run_supply_chain_analysis

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