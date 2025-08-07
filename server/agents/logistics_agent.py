# logistics_agent.py

import pandas as pd
from sqlalchemy import text
from ..utils.db import get_db_engine


def get_logistics_info(at_risk_supplier_id: int) -> str:
    """
    Checks for active or delayed shipments from an at-risk supplier.
    """
    try:
        engine = get_db_engine()
        query = text("SELECT * FROM shipments WHERE supplier_id = :supplier_id AND status != 'Delivered'")
        active_shipments = pd.read_sql(query, engine, params={'supplier_id': at_risk_supplier_id})
    except Exception as e:
        return f"Database error: {e}"

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