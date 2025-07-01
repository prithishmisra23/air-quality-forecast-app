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
CORS(app)

API_KEY = "b48771cc44eb3963dc408c3759655e2a" # Consider loading from environment variable for production

# Load ML model
try:
    # Ensure model.pkl is in the same directory as this script, or provide a full path
    model = joblib.load("model.pkl")
    print("✅ ML model loaded successfully.")
except Exception as e:
    print(f"❌ Failed to load model.pkl: {e}. The /api/predict endpoint will not work.")
    model = None # Set to None if loading fails

# Real-Time AQI Endpoint
@app.route("/api/aqi", methods=["GET"])
def get_aqi():
    city = request.args.get("city")
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if city:
        # ✅ Use hardcoded coordinates for Delhi
        if city.lower() == "delhi":
            lat, lon = 28.6139, 77.2090
        else:
            geolocator = Nominatim(user_agent="aqi_app")
            try:
                location = geolocator.geocode(city, timeout=10)
            except Exception as e:
                # Log the error for server-side debugging
                print(f"Geocoding error for city '{city}': {e}")
                return jsonify({"error": f"Geocoding error for '{city}': {e}"}), 500
            if not location:
                return jsonify({"error": f"City '{city}' not found."}), 404
            lat, lon = location.latitude, location.longitude

    if lat and lon:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        try:
            res = requests.get(url)
            res.raise_for_status()
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
        components = data["list"][0].get("components", {})

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
    if not city: # If no city provided, default to Delhi (as per previous logic)
        city = "Delhi"

    geolocator = Nominatim(user_agent="aqi_app")
    try:
        location = geolocator.geocode(city, timeout=10) # Added timeout
    except Exception as e:
        print(f"Geocoding error for city '{city}' (history): {e}")
        return jsonify({"error": f"Geocoding error for '{city}': {e}"}), 500
    if not location:
        return jsonify({"error": f"City '{city}' not found."}), 404

    lat, lon = location.latitude, location.longitude
    history_data = []

    # OpenWeatherMap history API works with 'start' and 'end' UNIX timestamps.
    # To get daily average, we need to request for specific periods.
    # The current implementation gets data for the first hour of each day.
    # If you need a full day's average, you'd need to fetch more data points
    # within the day and average them. For simplicity, keeping the existing logic
    # but acknowledging it only takes one hour's data.

    for i in range(7):
        # Go back 'i+1' days from current UTC time
        date_utc = datetime.utcnow() - timedelta(days=i + 1)
        # Get timestamp for the beginning of the day (UTC)
        dt_start = int(date_utc.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        # Get timestamp for one hour later (or end of day if you want average)
        dt_end = dt_start + 3600 # Fetches data for the first hour of the day

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

@app.route('/api/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({"error": "ML model not loaded. Prediction is unavailable."}), 503

    data = request.get_json()
    # Define the expected features for your model prediction
    # Ensure these keys match exactly what your model was trained on
    # and what the frontend sends.
    required_features = ["pm25", "pm10", "no2", "so2", "co", "o3"] # Removed 'no' and 'nh3' as per frontend's prior payload
                                                                # If your model needs them, you MUST add them here and in frontend
    features_dict = {}
    for feature in required_features:
        try:
            # Get the value from the incoming JSON, convert to float
            val = float(data.get(feature))
            features_dict[feature] = val
        except (TypeError, ValueError):
            return jsonify({"error": f"Missing or invalid value for '{feature}' in prediction request."}), 400

    try:
        # Create a DataFrame with the correct feature names and order
        features_df = pd.DataFrame([features_dict])
        prediction = model.predict(features_df)[0]
        return jsonify({"prediction": round(prediction, 2)}) # Changed 'predicted_aqi' to 'prediction'
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        # More specific error for prediction failure due to model input
        return jsonify({"error": f"Prediction failed due to model error: {str(e)}"}), 500

if __name__ == "__main__":
    # Use 0.0.0.0 for external access in Docker/Render, or 127.0.0.1 for local
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
