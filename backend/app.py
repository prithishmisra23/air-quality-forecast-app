from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import pandas as pd
import joblib
import numpy as np

app = Flask(__name__)
CORS(app)

API_KEY = "b48771cc44eb3963dc408c3759655e2a"

# Load ML model
model = joblib.load("model.pkl")

# AQI Route
@app.route("/api/aqi", methods=["GET"])
def get_aqi():
    city = request.args.get("city")
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if city:
        geolocator = Nominatim(user_agent="aqi_app")
        location = geolocator.geocode(city)
        if not location:
            return jsonify({"error": "Invalid city"}), 404
        lat, lon = location.latitude, location.longitude

    if lat and lon:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        res = requests.get(url)
        data = res.json()

        if "list" not in data or not data["list"]:
            return jsonify({"error": "No AQI data available"}), 404

        components = data["list"][0]["components"]
        aqi = data["list"][0]["main"]["aqi"]

        return jsonify({
            "lat": float(lat),
            "lon": float(lon),
            "aqi": aqi,
            "components": components
        })
    else:
        return jsonify({"error": "Missing location parameters"}), 400

# History Route
@app.route("/api/history", methods=["GET"])
def get_history():
    city = request.args.get("city", "Delhi")
    geolocator = Nominatim(user_agent="aqi_app")
    location = geolocator.geocode(city)
    if not location:
        return jsonify({"error": "Invalid city"}), 404

    lat, lon = location.latitude, location.longitude
    history_data = []

    for i in range(7):
        dt = int((datetime.utcnow() - timedelta(days=i+1)).timestamp())
        url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={dt}&end={dt + 3600}&appid={API_KEY}"
        res = requests.get(url)
        data = res.json()

        if "list" in data and data["list"]:
            aqi_val = data["list"][0]["main"]["aqi"]
            history_data.append({"date": (datetime.utcnow() - timedelta(days=i+1)).strftime("%Y-%m-%d"), "aqi": aqi_val})

    return jsonify(history_data[::-1])

# Prediction Route
@app.route("/api/predict", methods=["POST"])
def predict_aqi():
    try:
        input_data = request.json
        values = [input_data[col] for col in ['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']]
        prediction = model.predict([values])[0]
        return jsonify({"predicted_aqi": int(prediction)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render assigns the port
    app.run(host='0.0.0.0', port=port, debug=True)



