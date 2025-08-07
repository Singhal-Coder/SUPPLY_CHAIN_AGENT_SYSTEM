# demand_agent.py

import pandas as pd
from prophet import Prophet
import logging
from pathlib import Path

# Suppress verbose logging from Prophet
logging.getLogger('cmdstanpy').setLevel(logging.ERROR)

PRODUCT_DATA_FILE = Path(__file__).parent.parent / 'data' / 'products.csv'
SALES_HISTORY_FILE = Path(__file__).parent.parent / 'data' / 'sales_history.csv'

def get_demand_forecast(at_risk_supplier_id: int) -> str:
    """
    Finds products linked to a supplier and forecasts future demand using Prophet.
    """
    try:
        df_products = pd.read_csv(PRODUCT_DATA_FILE)
        df_sales = pd.read_csv(SALES_HISTORY_FILE, parse_dates=['ds'])
    except FileNotFoundError as e:
        return f"Data file not found: {e}"

    # 1. Find the product ID for the given supplier
    product_info = df_products[df_products['supplier_id'] == at_risk_supplier_id]
    if product_info.empty:
        return "" # No products linked to this supplier

    # For simplicity, we'll forecast the first product found for this supplier
    product_id = product_info.iloc[0]['product_id']
    product_name = product_info.iloc[0]['product_name']
    
    # 2. Get the sales history for that specific product
    product_sales_history = df_sales[df_sales['product_id'] == product_id].copy()
    if len(product_sales_history) < 10: # Need enough data to forecast
        return f"Insufficient sales history for {product_name}."

    print(f"   📦 Demand Agent: Forecasting demand for '{product_name}'...")
    
    # 3. Build and train the Prophet forecasting model
    # Prophet is designed to be robust and works well with default settings
    model = Prophet(weekly_seasonality=True, daily_seasonality=False)
    model.fit(product_sales_history)
    
    # 4. Make a future prediction (4 weeks ahead)
    future = model.make_future_dataframe(periods=4, freq='W')
    forecast = model.predict(future)
    
    # 5. Analyze the forecast to generate an insight
    # Get the last actual sales number
    current_sales = product_sales_history['y'].iloc[-1]
    # Get the final forecasted sales number
    predicted_sales = int(forecast['yhat'].iloc[-1])
    
    # Calculate the percentage change
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