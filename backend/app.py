from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import datetime
import random
from joblib import load

app = Flask(__name__)
CORS(app)

API_KEY = "b48771cc44eb3963dc408c3759655e2a"

# Load model once at startup
model = load('model.pkl')

@app.route('/api/aqi', methods=['GET'])
def get_aqi():
    city = request.args.get('city')

    if not city:
        return jsonify({'error': 'City parameter is missing'}), 400

    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    try:
        geo_response = requests.get(geo_url)
        geo_response.raise_for_status()
        geo_data = geo_response.json()

    if not geo_data or not isinstance(geo_data, list) or len(geo_data) == 0:
    return jsonify({'error': f'City "{city}" not found'}), 404

    lat = geo_data[0].get('lat')
    lon = geo_data[0].get('lon')

    if lat is None or lon is None:
    return jsonify({'error': f'Coordinates for "{city}" not found'}), 404

        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']

        url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        if 'list' not in data or not data['list']:
            return jsonify({'error': 'Invalid API response structure'}), 500

        components = data['list'][0]['components']
        aqi = data['list'][0]['main']['aqi']

        return jsonify({'aqi': aqi, 'components': components})

    except requests.exceptions.RequestException as e:
        print("❌ Network/API error:", str(e))
        return jsonify({'error': 'Failed to fetch AQI data', 'details': str(e)}), 500
    except Exception as e:
        print("❌ Unexpected error:", str(e))
        return jsonify({'error': 'Internal error', 'details': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    history = []
    today = datetime.datetime.today()
    for i in range(7):
        date = (today - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        aqi_value = random.randint(50, 200)
        history.append({'date': date, 'aqi': aqi_value})
    history.reverse()
    return jsonify({'history': history})

@app.route('/api/predict', methods=['POST'])
def predict_aqi():
    try:
        data = request.get_json()
        pm2_5 = data.get('pm2_5', 50)
        humidity = data.get('humidity', 70)
        temp = data.get('temp', 30)

        prediction = model.predict([[pm2_5, humidity, temp]])[0]
        return jsonify({'predicted_aqi': round(prediction)})

    except Exception as e:
        print("❌ Prediction error:", str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
