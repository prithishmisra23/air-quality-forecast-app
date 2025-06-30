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
        return jsonify({'error': 'City is required'}), 400

    # Geocode to get coordinates
    location = geolocator.geocode(city)
    if not location:
        return jsonify({'error': 'Invalid city name'}), 400

    lat = location.latitude
    lon = location.longitude

    # Fetch AQI data using coordinates
    aqi_data = fetch_current_aqi(lat, lon)
    if not aqi_data:
        return jsonify({'error': 'Could not fetch AQI data'}), 500

    return jsonify({
        'aqi': aqi_data['aqi'],
        'components': aqi_data['components'],
        'lat': lat,
        'lon': lon
    })

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
