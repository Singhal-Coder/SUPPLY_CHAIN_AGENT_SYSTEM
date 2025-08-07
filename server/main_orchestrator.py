import re
import pycountry

# Import the functions from our agent files
from agents.supplier_agent import find_at_risk_suppliers
from agents.risk_agent import get_risk_summary
from agents.demand_agent import get_demand_forecast
from agents.logistics_agent import get_logistics_info

def get_country_code(country_name: str) -> str:
    """
    Converts a country name to its 2-letter alpha_2 code using pycountry.
    Includes fuzzy searching for common mismatches.
    """
    try:
        # First, try a direct lookup
        country = pycountry.countries.get(name=country_name)
        if country:
            return country.alpha_2.lower()
        
        # If direct lookup fails, try a fuzzy search
        country = pycountry.countries.search_fuzzy(country_name)
        if country:
            return country[0].alpha_2.lower()
            
    except Exception:
        # If everything fails, return a default
        pass
        
    print(f"   [Warning] Could not find country code for '{country_name}'. Defaulting to 'us'.")
    return "us"

def run_supply_chain_analysis(user_api_key: str, user_project_id: str):
    """
    The main orchestrator logic. Returns a list of alert strings.
    """
    print("📈 Master Orchestrator: Starting supply chain analysis...")
    alerts = [] # Create a list to hold our alert strings

    # 1. Get the list of at-risk suppliers
    at_risk_suppliers = find_at_risk_suppliers()
    
    if at_risk_suppliers.empty:
        message = "✅ Analysis Complete: No high-risk suppliers found."
        print(message)
        return [message]

    # 2. For each at-risk supplier, get a risk summary
    for index, supplier in at_risk_suppliers.iterrows():
        supplier_id = supplier['supplier_id']
        supplier_name = supplier['supplier_name']
        country = supplier['country']
        status = supplier['production_status']
        final_score = supplier['risk_score']
        # Convert country name to 2-letter code for the API
        country_code = get_country_code(country)

        # 3. Get the demand impact
        demand_forecast_info = get_demand_forecast(supplier_id)

        # 4. Get the logistics information
        logistics_alert_info = get_logistics_info(supplier_id)

        # 5. Get the risk summary
        if status == 'DELAYED':
            topic = "shipping delay OR port congestion"
        else:
            topic = "supply chain disruption OR factory shutdown"
        # Call the Global Risk Agent
        risk_summary_data = get_risk_summary(topic, country_code, user_api_key, user_project_id)
        # Analyze demand forecast


        priority_level = "🟢 LOW"
        if "error" in risk_summary_data:
            news_summary_text = risk_summary_data["error"]
            risk_category = "Error"
            key_entities = []
        else:
            # Analyze risk category from news
            risk_category = risk_summary_data.get("risk_category", "Other")
            if risk_category in ['Logistics', 'Natural Disaster', 'Geopolitical']:
                final_score += 5 # High impact categories
            elif risk_category == 'Financial':
                final_score += 2 # Medium impact

            news_summary_text = risk_summary_data.get('summary', 'N/A')
            key_entities = risk_summary_data.get('key_entities', [])




        if demand_forecast_info and "increase" in demand_forecast_info:
            # Find numbers in the forecast string
            numbers = re.findall(r'\d+', demand_forecast_info)
            if numbers:
                percent_increase = int(numbers[0])
                if percent_increase > 25:
                    final_score += 5 # Major demand spike
                elif percent_increase > 10:
                    final_score += 2 # Moderate demand spike


        # Analyze logistics status
        if logistics_alert_info and "Delayed" in logistics_alert_info:
            final_score += 3 # Active shipment is delayed

        # Determine final priority level based on score
        if final_score > 15:
            priority_level = "🔴 CRITICAL"
        elif final_score > 10:
            priority_level = "🟠 HIGH"
        elif final_score > 5:
            priority_level = "🟡 MEDIUM"
        else:
            priority_level = "🟢 LOW"
        # --- REASONING ENGINE END ---

        # --- 3. BUILD THE FINAL ALERT ---
        alert_string = f"{priority_level} ALERT FOR: {supplier_name.upper()}\n"
        alert_string += f"   - Supplier Status: {status} (Internal Risk Score: {supplier['risk_score']})\n"
        if demand_forecast_info:
            alert_string += f"   - {demand_forecast_info}\n"
        if logistics_alert_info:
            alert_string += f"   - {logistics_alert_info}\n"
        alert_string += f"   - External Risk Category: {risk_category}\n"
        alert_string += f"   - Key Entities: {', '.join(key_entities)}\n"
        alert_string += f"   - News Summary: {news_summary_text}\n"
        
        alerts.append(alert_string)
        print(f"Generated '{priority_level}' alert for {supplier_name}")

    if not alerts:
        message = "✅ Analysis Complete: No high-risk suppliers found."
        print(message)
        return [message]
        
    return alerts

if __name__ == "__main__":
    run_supply_chain_analysis()