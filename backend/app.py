from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import joblib
import pandas as pd
import datetime
import numpy as np

app = Flask(__name__)
CORS(app)

# Load trained model
model = joblib.load("model.pkl")

# Your OpenWeatherMap API key
API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"

# Sample 7-day AQI history data
aqi_history = [
    {"date": (datetime.date.today() - datetime.timedelta(days=i)).strftime("%Y-%m-%d"), "aqi": int(150 + np.random.randint(-25, 25))}
    for i in range(6, -1, -1)
]

@app.route('/')
def home():
    return "✅ Air Quality Flask Backend Running!"

@app.route('/api/aqi', methods=['GET'])
def get_aqi():
    try:
        city = request.args.get("city")
        lat = request.args.get("lat")
        lon = request.args.get("lon")

        if city:
            geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
            geo_res = requests.get(geocode_url).json()
            if not geo_res:
                return jsonify({"error": "City not found"}), 404
            lat, lon = geo_res[0]['lat'], geo_res[0]['lon']

        if not (lat and lon):
            return jsonify({"error": "Latitude and Longitude required"}), 400

        air_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        air_res = requests.get(air_url).json()
        if 'list' not in air_res or not air_res['list']:
            return jsonify({"error": "No AQI data available"}), 404

        aqi_data = air_res['list'][0]
        aqi_value = aqi_data['main']['aqi']
        components = aqi_data['components']

        return jsonify({
            "lat": float(lat),
            "lon": float(lon),
            "aqi": aqi_value * 50,  # scaled to 0–500
            "components": components
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify({"history": aqi_history})

@app.route('/api/predict', methods=['POST'])
def predict_aqi():
    try:
        data = request.get_json()
        pm25 = float(data.get("pm2_5", 50))
        humidity = float(data.get("humidity", 50))
        temp = float(data.get("temp", 25))

        input_data = pd.DataFrame([[pm25, humidity, temp]], columns=["pm2_5", "humidity", "temp"])
        prediction = model.predict(input_data)[0]
        return jsonify({"predicted_aqi": round(prediction, 2)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render assigns the port
    app.run(host='0.0.0.0', port=port, debug=True)

