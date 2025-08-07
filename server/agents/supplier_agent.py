import pandas as pd
from sqlalchemy import text
from ..utils.db import get_db_engine 

# --- Configuration ---
RISK_THRESHOLD = 7.0

# --- Agent Logic ---
def find_at_risk_suppliers() -> pd.DataFrame:
    """
    Reads the supplier data and identifies suppliers at high risk.
    """
    print("\n🏭 Supplier Agent: Analyzing supplier data...")
    
    try:
        engine = get_db_engine()
        query = text("SELECT * FROM suppliers;")
        df = pd.read_sql(query, engine)
    except Exception as e:
        print(f"Error reading from database: {e}")
        return pd.DataFrame()

    # 2. Define risk criteria
    # A supplier is at risk if its status is not 'OK' OR its risk score is too high.
    at_risk_criteria = (df['production_status'] != 'OK') | (df['risk_score'] >= RISK_THRESHOLD)
    
    at_risk_suppliers = df[at_risk_criteria]
    
    if not at_risk_suppliers.empty:
        print(f"   Found {len(at_risk_suppliers)} suppliers matching risk criteria.")
    else:
        print("   No suppliers are currently at high risk.")
        
    return at_risk_suppliers


# --- To run this agent standalone for testing ---
if __name__ == "__main__":
    high_risk_list = find_at_risk_suppliers()

    print("\n--- AGENT OUTPUT ---")
    if not high_risk_list.empty:
        print(high_risk_list)
    else:
        print("All suppliers are operating normally.")
    print("--------------------")