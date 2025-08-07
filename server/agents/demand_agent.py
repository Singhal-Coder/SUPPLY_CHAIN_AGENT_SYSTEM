# demand_agent.py

import pandas as pd
from prophet import Prophet
import logging
from sqlalchemy import text
from ..utils.db import get_db_engine

# Suppress verbose logging from Prophet
logging.getLogger('cmdstanpy').setLevel(logging.ERROR)

def get_demand_forecast(at_risk_supplier_id: int) -> str:
    """
    Finds products linked to a supplier and forecasts future demand using Prophet.
    """
    try:
        engine = get_db_engine()
        # Read both products and sales history from the database
        products_query = text("SELECT * FROM products WHERE supplier_id = :supplier_id")
        sales_query = text("SELECT * FROM sales_history")
        
        df_products = pd.read_sql(products_query, engine, params={'supplier_id': at_risk_supplier_id})
        df_sales = pd.read_sql(sales_query, engine, parse_dates=['ds'])

    except Exception as e:
        return f"Database error: {e}"

    if df_products.empty:
        return ""

    # For simplicity, we'll forecast the first product found for this supplier
    product_id = df_products.iloc[0]['product_id']
    product_name = df_products.iloc[0]['product_name']
    
    product_sales_history = df_sales[df_sales['product_id'] == product_id].copy()
    if len(product_sales_history) < 10:
        return f"Insufficient sales history for {product_name}."

    print(f"   📦 Demand Agent: Forecasting demand for '{product_name}'...")
    
    # 3. Build and train the Prophet forecasting model
    # Prophet is designed to be robust and works well with default settings
    model = Prophet(weekly_seasonality=True, daily_seasonality=False)
    model.fit(product_sales_history)
    
    # 4. Make a future prediction (4 weeks ahead)
    future = model.make_future_dataframe(periods=4, freq='W')
    forecast = model.predict(future)
    
    current_sales = product_sales_history['y'].iloc[-1]
    predicted_sales = int(forecast['yhat'].iloc[-1])
    
    percentage_change = round(((predicted_sales - current_sales) / current_sales) * 100)
    
    trend = "increase" if percentage_change >= 0 else "decrease"
    
    forecast_statement = (
        f"DEMAND FORECAST for '{product_name}': Sales are projected to be ~{predicted_sales} units/week "
        f"in 4 weeks, a {percentage_change}% {trend} from current levels."
    )
    
    return forecast_statement


if __name__ == "__main__":
    # We will test with a supplier ID that we know has historical sales data (e.g., 1005)
    test_supplier_id = 1005  # This supplier makes the 'Alpha Smartwatch'

    print(f"--- Running a standalone test for the Demand Agent ---")
    print(f"Testing with Supplier ID: {test_supplier_id}")
    
    # Call the main function
    forecast_result = get_demand_forecast(test_supplier_id)
    
    print("\n--- AGENT OUTPUT ---")
    print(forecast_result)
    print("--------------------")