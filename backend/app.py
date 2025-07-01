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

API_KEY = "b48771cc44eb3963dc408c3759655e2a"

# Load ML model
try:
    model = joblib.load("model.pkl")
    print("✅ ML model loaded successfully.")
except Exception as e:
    print(f"❌ Failed to load model.pkl: {e}")
    model = None

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
                return jsonify({"error": f"Geocoding error: {e}"}), 500
            if not location:
                return jsonify({"error": "City not found."}), 404
            lat, lon = location.latitude, location.longitude

    if lat and lon:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        try:
            res = requests.get(url)
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            return jsonify({"error": f"Failed to fetch AQI: {e}"}), 500

        if "list" not in data or not data["list"]:
            return jsonify({"error": "No AQI data found."}), 404

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
    city = request.args.get("city", "Delhi")
    geolocator = Nominatim(user_agent="aqi_app")
    try:
        location = geolocator.geocode(city)
    except Exception as e:
        return jsonify({"error": f"Geocoding error: {e}"}), 500
    if not location:
        return jsonify({"error": "City not found."}), 404

    lat, lon = location.latitude, location.longitude
    history_data = []

    for i in range(7):
        date_utc = datetime.utcnow() - timedelta(days=i + 1)
        dt_start = int(date_utc.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        dt_end = dt_start + 3600

        url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={dt_start}&end={dt_end}&appid={API_KEY}"
        try:
            res = requests.get(url)
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            print(f"History fetch failed for {date_utc.date()}: {e}")
            continue

        if "list" in data and data["list"]:
            entry = data["list"][0]
            aqi_val = entry["main"].get("aqi")
            if aqi_val is not None:
                history_data.append({
                    "date": date_utc.strftime("%Y-%m-%d"),
                    "aqi": aqi_val
                })

    return jsonify(history_data[::-1])  # Oldest to newest

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json()
    try:
        features = pd.DataFrame([{
            "pm25": float(data.get("pm25")),
            "pm10": float(data.get("pm10")),
            "no2": float(data.get("no2")),
            "so2": float(data.get("so2")),
            "co": float(data.get("co")),
            "o3": float(data.get("o3"))
        }])
        prediction = model.predict(features)[0]
        return jsonify({"prediction": round(prediction, 2)})
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
