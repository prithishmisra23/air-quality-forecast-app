from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import datetime
import random

app = Flask(__name__)
CORS(app)

API_KEY = "b48771cc44eb3963dc408c3759655e2a"

@app.route('/api/aqi', methods=['GET'])
def get_aqi():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # This will raise an error if API fails

        data = response.json()

        # Check if the response has valid data
        if 'list' not in data or not data['list']:
            return jsonify({'error': 'Invalid API response structure'}), 500

        components = data['list'][0]['components']
        aqi = data['list'][0]['main']['aqi']

        return jsonify({'aqi': aqi, 'components': components})

    except Exception as e:
        print("❌ Error fetching AQI data:", str(e))  # Shows in terminal
        return jsonify({'error': 'API fetch failed', 'details': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    # Simulating past 7 days AQI values (normally fetched from a database or premium API)
    history = []
    today = datetime.datetime.today()
    for i in range(7):
        date = (today - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        aqi_value = random.randint(50, 200)
        history.append({'date': date, 'aqi': aqi_value})
    history.reverse()
    return jsonify({'history': history})
    from joblib import load  # Add this at the top if not already

@app.route('/api/predict', methods=['POST'])
def predict_aqi():
    try:
        data = request.get_json()
        pm2_5 = data.get('pm2_5', 50)
        humidity = data.get('humidity', 70)
        temp = data.get('temp', 30)

        model = load('model/model.pkl')
        prediction = model.predict([[pm2_5, humidity, temp]])[0]
        return jsonify({'predicted_aqi': round(prediction)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)

