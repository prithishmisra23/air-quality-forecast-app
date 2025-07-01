# app.py (Flask Backend)

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import pandas as pd
import joblib
import numpy as np
import os

app = Flask(__name__)
CORS(app) # Enable CORS for communication with your Streamlit frontend

API_KEY = "b48771cc44eb3963dc408c3759655e2a" # IMPORTANT: Consider loading this from environment variables for production!

# Load ML model
try:
    # --- FIX: Model loading path adjusted to 'model.pkl' ---
    # Ensure the 'model' directory exists and 'model.pkl' is inside it relative to app.py
    model = joblib.load("model.pkl")
    print("✅ ML model loaded successfully from model.pkl.")
except Exception as e:
    print(f"❌ Failed to load model.pkl: {e}. The /api/predict endpoint will not work.")
    model = None # Set to None if loading fails, so the endpoint can return an error

# Real-Time AQI Endpoint
@app.route("/api/aqi", methods=["GET"])
def get_aqi():
    city = request.args.get("city")
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    # If city is provided, try to get coordinates
    if city:
        # Special handling for Delhi to use hardcoded coordinates (as per your original logic)
        if city.lower() == "delhi":
            lat, lon = 28.6139, 77.2090
        else:
            geolocator = Nominatim(user_agent="aqi_app", timeout=10) # Added timeout
            try:
                location = geolocator.geocode(city)
            except Exception as e:
                # Log the error for server-side debugging
                print(f"Geocoding error for city '{city}': {e}")
                return jsonify({"error": f"Geocoding error for '{city}': {e}"}), 500
            if not location:
                return jsonify({"error": f"City '{city}' not found."}), 404
            lat, lon = location.latitude, location.longitude

    # If coordinates are available (either from city lookup or directly provided)
    if lat and lon:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        try:
            res = requests.get(url)
            res.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = res.json()
        except requests.exceptions.RequestException as e:
            # Log the error for server-side debugging
            print(f"Failed to fetch AQI from OpenWeatherMap for ({lat}, {lon}): {e}")
            return jsonify({"error": f"Failed to fetch AQI data: {e}"}), 500
        except Exception as e:
            print(f"An unexpected error occurred processing AQI for ({lat}, {lon}): {e}")
            return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

        if "list" not in data or not data["list"]:
            return jsonify({"error": "No AQI data found for the given coordinates."}), 404

        aqi = data["list"][0]["main"]["aqi"]
        components = data["list"][0].get("components", {}) # Use .get() for safety

        return jsonify({
            "lat": float(lat),
            "lon": float(lon),
            "aqi": aqi,
            "components": components
        })

    return jsonify({"error": "Missing coordinates or city name."}), 400


# 7-Day History Endpoint
@app.route("/api/history", methods=["GET"])
def get_history():
    city = request.args.get("city")
    if not city: # If no city provided, default to Delhi
        city = "Delhi"

    geolocator = Nominatim(user_agent="aqi_app", timeout=10) # Added timeout
    try:
        location = geolocator.geocode(city)
    except Exception as e:
        print(f"Geocoding error for city '{city}' (history): {e}")
        return jsonify({"error": f"Geocoding error for '{city}': {e}"}), 500
    if not location:
        return jsonify({"error": f"City '{city}' not found."}), 404

    lat, lon = location.latitude, location.longitude
    history_data = []

    # OpenWeatherMap history API works with 'start' and 'end' UNIX timestamps.
    # The current implementation fetches data for the first hour of each day.
    # If you need a full day's average, you would need to fetch more data points
    # within the day and average them out.
    for i in range(7):
        # Go back 'i+1' days from current UTC time
        date_utc = datetime.utcnow() - timedelta(days=i + 1)
        # Get timestamp for the beginning of the day (UTC)
        dt_start = int(date_utc.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        # Get timestamp for one hour later. This gets a single data point for the day.
        dt_end = dt_start + 3600

        url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={dt_start}&end={dt_end}&appid={API_KEY}"
        try:
            res = requests.get(url)
            res.raise_for_status()
            data = res.json()
        except requests.exceptions.RequestException as e:
            print(f"History fetch failed for {date_utc.date()} ({city}): {e}")
            continue # Skip this day if fetch fails
        except Exception as e:
            print(f"An unexpected error occurred processing history for {date_utc.date()} ({city}): {e}")
            continue

        if "list" in data and data["list"]:
            # Take the first available entry for that hour/day
            entry = data["list"][0]
            aqi_val = entry["main"].get("aqi")
            if aqi_val is not None:
                history_data.append({
                    "date": date_utc.strftime("%Y-%m-%d"), # Format date for frontend
                    "aqi": aqi_val
                })
    # Return data from oldest to newest for plotting
    return jsonify(history_data[::-1])

# AQI Prediction Endpoint
@app.route('/api/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({"error": "ML model not loaded. Prediction is unavailable."}), 503

    data = request.get_json()
    # --- FIX: Updated required_features to match your model's training data ---
    required_features = ["pm2_5", "humidity", "temperature"]
    
    features_dict = {}
    for feature in required_features:
        try:
            # Get the value from the incoming JSON payload, convert to float
            val = float(data.get(feature))
            features_dict[feature] = val
        except (TypeError, ValueError):
            # Return a 400 Bad Request error if a required feature is missing or invalid
            return jsonify({"error": f"Missing or invalid value for '{feature}' in prediction request. Expected features: {', '.join(required_features)}"}), 400

    try:
        # Create a Pandas DataFrame from the received features for model input
        # Ensure the column names in the DataFrame match what your model expects
        features_df = pd.DataFrame([features_dict])
        prediction = model.predict(features_df)[0]
        # Return the prediction. The key 'prediction' must match what frontend expects.
        return jsonify({"prediction": round(prediction, 2)})
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        # Return a 500 Internal Server Error if prediction itself fails
        return jsonify({"error": f"Prediction failed due to internal model error: {str(e)}"}), 500

# Main execution block
if __name__ == "__main__":
    # Use 0.0.0.0 to make the Flask app accessible externally (e.g., in Docker or Render)
    # Use 127.0.0.1 (localhost) if only running on your local machine
    port = int(os.environ.get("PORT", 5000)) # Use environment variable for port (e.g., for Render) or default to 5000
    app.run(host="0.0.0.0", port=port, debug=True) # debug=True is good for development, disable in production
