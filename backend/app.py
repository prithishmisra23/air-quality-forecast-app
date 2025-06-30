from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import pandas as pd # <-- Make sure pandas is imported
import joblib
import numpy as np
import os

app = Flask(__name__)
CORS(app)

API_KEY = "b48771cc44eb3963dc408c3759655e2a"

# Load ML model
try:
    model = joblib.load("model.pkl")
    print("Model loaded successfully!") # Added for debugging startup
except Exception as e:
    print(f"Error loading model.pkl: {e}")
    # Setting model to None will cause the predict route to return a 503 if loading fails
    model = None

# AQI Route
@app.route("/api/aqi", methods=["GET"])
def get_aqi():
    city = request.args.get("city")
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if city:
        geolocator = Nominatim(user_agent="aqi_app")
        try:
            location = geolocator.geocode(city)
        except Exception as e:
            return jsonify({"error": f"Geocoding error for city '{city}': {e}"}), 500
        
        if not location:
            return jsonify({"error": "Invalid city or city not found"}), 404
        lat, lon = location.latitude, location.longitude

    if lat and lon:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        try:
            res = requests.get(url)
            res.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            data = res.json()
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Error fetching AQI data from OpenWeatherMap: {e}"}), 500
        except ValueError: # Catches JSON decoding errors
            return jsonify({"error": "Invalid JSON response from OpenWeatherMap"}), 500


        if "list" not in data or not data["list"]:
            return jsonify({"error": "No AQI data available for this location"}), 404

        components = data["list"][0].get("components", {})
        aqi = data["list"][0]["main"]["aqi"]

        return jsonify({
            "lat": float(lat),
            "lon": float(lon),
            "aqi": aqi,
            "components": components
        })
    else:
        return jsonify({"error": "Missing location parameters (city, lat, or lon)"}), 400

# History Route
@app.route("/api/history", methods=["GET"])
def get_history():
    city = request.args.get("city", "Delhi") # Default to Delhi if no city provided
    geolocator = Nominatim(user_agent="aqi_app")
    try:
        location = geolocator.geocode(city)
    except Exception as e:
        return jsonify({"error": f"Geocoding error for city '{city}': {e}"}), 500

    if not location:
        return jsonify({"error": "Invalid city or city not found"}), 404

    lat, lon = location.latitude, location.longitude
    history_data = []

    for i in range(7): # Fetch data for the last 7 days
        # Calculate start of the day for (i+1) days ago in UTC
        target_date = datetime.utcnow() - timedelta(days=i + 1)
        start_of_day_utc = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        dt_start = int(start_of_day_utc.timestamp())
        
        dt_end = dt_start + 3600 # Fetching for 1 hour from start_of_day_utc
        
        url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={dt_start}&end={dt_end}&appid={API_KEY}"
        
        try:
            res = requests.get(url)
            res.raise_for_status()
            data = res.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching historical AQI data for day {i+1}: {e}")
            continue # Skip this day if fetching fails
        except ValueError:
            print(f"Invalid JSON response for historical AQI data for day {i+1}")
            continue

        if "list" in data and data["list"]:
            entry = data["list"][0]
            aqi_val = entry["main"].get("aqi", None)
            if aqi_val is not None:
                history_data.append({
                    "date": start_of_day_utc.strftime("%Y-%m-%d"), # Use the date of the start_of_day
                    "aqi": aqi_val
                })

    # Return data sorted from oldest to newest
    return jsonify(history_data[::-1])

# Prediction Route
@app.route("/api/predict", methods=["POST"])
def predict_aqi():
    if model is None:
        return jsonify({"error": "ML model not loaded. Prediction not available."}), 503 # Service Unavailable

    try:
        input_data = request.json
        # These must be the EXACT feature names and order used during model training
        # This list comes directly from your model's expected features.
        required_fields = ['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']

        for field in required_fields:
            if field not in input_data:
                # Log the missing field for easier debugging on Render
                print(f"Missing field in prediction request: {field}")
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Extract values in the correct order as floats
        values = [float(input_data[field]) for field in required_fields]

        # Convert the list of values into a Pandas DataFrame with column names
        # This is the crucial fix for the "FutureWarning: X does not have valid feature names"
        # and subsequent 500 error.
        input_df = pd.DataFrame([values], columns=required_fields)

        # Make the prediction
        prediction = model.predict(input_df)[0] # model.predict expects 2D array or DataFrame

        return jsonify({"predicted_aqi": int(prediction)})
    except ValueError as ve: # Catch specific value conversion errors
        print(f"ValueError in predict_aqi: {ve}")
        return jsonify({"error": f"Invalid input value type: {ve}. Ensure all fields are numbers."}), 400
    except Exception as e:
        # Catch any other unexpected errors during prediction
        print(f"Unhandled error in predict_aqi: {e}") # Log the specific error
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
