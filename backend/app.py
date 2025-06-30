from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import datetime
import random
from joblib import load
from geopy.geocoders import Nominatim

app = Flask(__name__)
CORS(app)

API_KEY = "b48771cc44eb3963dc408c3759655e2a"

# Load trained model
model = load('model.pkl')

@app.route('/api/aqi', methods=['GET'])
def get_aqi():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'City parameter missing'}), 400

    try:
        geolocator = Nominatim(user_agent="aqi_app")
        location = geolocator.geocode(city)
        if not location:
            return jsonify({'error': f'City "{city}" not found'}), 404

        lat = location.latitude
        lon = location.longitude

        url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        aqi = data['list'][0]['main']['aqi']
        components = data['list'][0]['components']

        return jsonify({
            'aqi': aqi,
            'components': components,
            'lat': lat,
            'lon': lon
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    city = request.args.get('city', 'Delhi')
    today = datetime.datetime.today()
    history = []
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
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
