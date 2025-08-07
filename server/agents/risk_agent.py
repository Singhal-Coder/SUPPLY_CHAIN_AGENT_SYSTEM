import os
import json
import redis
from dotenv import load_dotenv
from ibm_watson_machine_learning.foundation_models import Model
from newsdataapi import NewsDataApiClient
from sqlalchemy.exc import ProgrammingError

# --- Configuration ---
# Load credentials from the .env file
load_dotenv()
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")

try:
    redis_client = redis.from_url(REDIS_URL)
    print("✅ Successfully connected to Redis cache.")
except Exception as e:
    print(f"⚠️ Could not connect to Redis. Caching will be disabled. Error: {e}")
    redis_client = None

model_id = "ibm/granite-3-3-8b-instruct"
parameters = {
    "decoding_method": "greedy",
    "max_new_tokens": 1024,
    "min_new_tokens": 50,
    "repetition_penalty": 1,
}

def get_risk_summary(risk_topic: str, country_code: str, user_api_key: str = WATSONX_API_KEY, user_project_id: str = WATSONX_PROJECT_ID) -> dict:
    """
    Fetches news using Newsdata.io and returns an AI-generated summary.
    """
    print(f"\n🌍 Global Risk Agent: Scanning Newsdata.io for '{risk_topic}' in '{country_code}'...")

    cache_key = f"news_risk:{risk_topic}:{country_code}"
    if redis_client:
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                print(f"   [CACHE HIT] Found result for key: {cache_key}")
                return json.loads(cached_result) # Return saved result immediately
        except Exception as e:
            print(f"   [CACHE WARNING] Could not read from Redis. Bypassing cache. Error: {e}")

    print(f"   [CACHE MISS] No result found for key: {cache_key}. Fetching from APIs...")



    try:
        api = NewsDataApiClient(apikey=NEWSDATA_API_KEY)
        
        response = api.latest_api(q=risk_topic, country=country_code, language='en')
        
        print(f"   [DEBUG] API Response Status: {response.get('status')}")
        print(f"   [DEBUG] Total Results Found: {response.get('totalResults')}")

        if response.get('status') != 'success':
            api_error_message = response.get('results', {}).get('message', 'Unknown API Error')
            return {"error": f"API Error: {api_error_message}"}

        articles = response.get('results', [])
        if not articles:
            return {"error": "No news found for the given criteria."}


        articles_content = [f"{article['title']}. {article.get('description', '')}" for article in articles]
        articles_text = " ".join(articles_content)
        print(f"   Found {len(articles)} relevant articles.")

    except Exception as e:
        print(f"   [DEBUG] An exception occurred while calling the API.")
        return {"error": f"An API exception occurred: {e}"}

    prompt = f"""
    Read the following news articles. 
    First, in a <think> block, reason about the content. Identify the main topic, potential risks, and key entities.
    Then, based on your thinking, provide the final structured JSON object inside a <response> block.

    The JSON object must have exactly three keys: "summary", "risk_category", and "key_entities".
    - "summary": A one-paragraph summary of the key events.
    - "risk_category": Classify the main risk type. Choose ONLY one from: 'Logistics', 'Financial', 'Geopolitical', 'Cybersecurity', 'Natural Disaster', or 'Other'.
    - "key_entities": A list of up to 3 important company names, locations, or organizations mentioned.

    News Articles to analyze: "{articles_text}"
    """

    try:
        model = Model(
            model_id=model_id,
            params=parameters,
            credentials={"apikey": user_api_key, "url": "https://us-south.ml.cloud.ibm.com"},
            project_id=user_project_id
        )
        generated_text = model.generate_text(prompt)
        print("   watsonx.ai generated a structured response.")
        
        try:
            start_tag = "<response>"
            end_tag = "</response>"
            start_index = generated_text.find(start_tag)
            end_index = generated_text.find(end_tag)
            
            if start_index != -1 and end_index != -1:
                # Extract the content between the tags
                response_content = generated_text[start_index + len(start_tag):end_index].strip()
                # The content might be a JSON object directly or a code block containing JSON
                json_string = response_content.strip('` \njson')
                result_dict = json.loads(json_string)

                if redis_client:
                    try:
                        # Cache the result for 1 hour (3600 seconds)
                        redis_client.set(cache_key, json.dumps(result_dict), ex=3600)
                        print(f"   [CACHE SET] Saved result for key: {cache_key}")
                    except Exception as e:
                        print(f"   [CACHE WARNING] Could not write to Redis. Error: {e}")

                return result_dict
            else:
                return {"error": "AI did not return a valid <response> block."}
        except Exception as e:
             return {"error": f"Failed to parse JSON from AI response: {e}"}

    except Exception as e:
        if isinstance(e, ProgrammingError) and "token_quota_reached" in str(e):
             return {"error": "Watsonx.ai token quota has been reached."}
        return {"error": f"Error connecting to watsonx.ai: {e}"}


if __name__ == "__main__":
    print("--- RUNNING A DEFINITIVE TEST WITH NEWSDATA.IO ---")
    topic_to_check = "technology" 
    country_to_check = "us"
    
    final_summary = get_risk_summary(topic_to_check, country_to_check)
    
    print("\n--- AGENT OUTPUT ---")
    print(final_summary)
    print("--------------------")