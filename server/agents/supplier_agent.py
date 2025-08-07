import pandas as pd
from pathlib import Path    

# --- Configuration ---
SUPPLIER_DATA_FILE = Path(__file__).parent.parent / 'data' / 'suppliers.csv'
RISK_THRESHOLD = 7.0 # We'll flag any supplier with a risk score above this

# --- Agent Logic ---
def find_at_risk_suppliers() -> pd.DataFrame:
    """
    Reads the supplier data and identifies suppliers at high risk.
    """
    print("\n🏭 Supplier Agent: Analyzing supplier data...")
    
    try:
        # 1. Read the supplier data from the CSV file
        df = pd.read_csv(SUPPLIER_DATA_FILE)
    except FileNotFoundError:
        print(f"Error: The file '{SUPPLIER_DATA_FILE}' was not found.")
        return pd.DataFrame() # Return an empty DataFrame

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