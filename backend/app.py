from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import joblib
import os

app = Flask(__name__)
CORS(app)

# Load the model
try:
    model = joblib.load("model.pkl")
    print("✅ Model loaded successfully")
except Exception as e:
    print("❌ Error loading model:", e)
    model = None

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Welcome to the Air Quality Prediction API"}), 200

@app.route("/api/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500

    try:
        data = request.get_json()
        print("📩 Received data:", data)

        pm25 = float(data.get("pm2_5", 50))
        humidity = float(data.get("humidity", 50))
        temp = float(data.get("temp", 25))

        input_df = pd.DataFrame([[pm25, humidity, temp]], columns=["pm2_5", "humidity", "temp"])
        print("📊 Input for model:", input_df)

        prediction = model.predict(input_df)[0]
        print("✅ Prediction:", prediction)

        return jsonify({"predicted_aqi": round(prediction, 2)}), 200

    except Exception as e:
        print("❌ Prediction error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
