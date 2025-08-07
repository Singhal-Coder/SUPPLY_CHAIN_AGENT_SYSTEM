# logistics_agent.py

import pandas as pd
from pathlib import Path

SHIPMENT_DATA_FILE = Path(__file__).parent.parent / 'data' / 'shipments.csv'

def get_logistics_info(at_risk_supplier_id: int) -> str:
    """
    Checks for active or delayed shipments from an at-risk supplier.
    """
    try:
        df_shipments = pd.read_csv(SHIPMENT_DATA_FILE)
    except FileNotFoundError:
        return "Shipment data file not found."

    # Find shipments from the supplier that are not yet delivered
    active_shipments = df_shipments[
        (df_shipments['supplier_id'] == at_risk_supplier_id) &
        (df_shipments['status'] != 'Delivered')
    ]

    if not active_shipments.empty:
        # For simplicity, we'll just report on the first found shipment
        shipment = active_shipments.iloc[0]
        shipment_id = shipment['shipment_id']
        status = shipment['status']
        risk_level = shipment['route_risk_level']
        
        logistics_alert = f"LOGISTICS ALERT: Shipment '{shipment_id}' is currently '{status}' on a '{risk_level}' risk route."
        print(f"   🚚 Logistics Agent: Found active shipment for supplier {at_risk_supplier_id}.")
        return logistics_alert

    return "" # Return empty string if no active shipments