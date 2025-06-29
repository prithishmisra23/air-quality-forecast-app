<details> <summary>Click here to copy the full README</summary>
# 🌫️ Air Quality Visualizer & Forecast App

A real-time air quality monitoring and forecasting app built using **Streamlit**, **Flask**, **OpenWeatherMap API**, and a **machine learning model**. This tool provides **live AQI data**, **forecast predictions**, **component breakdowns**, and **visual insights** for any location in the world.

---

## 🚀 Features

- 📍 **Location-based AQI**
- 📊 **7-day AQI forecast using ML**
- 🌐 **Real-time pollutant data (PM2.5, PM10, CO, NO₂, etc.)**
- 📈 **Graphs & visualizations (via Plotly)**
- 💾 **AQI data logged & downloadable as CSV**
- 🧠 **Backend API built with Flask**
- 📦 **Fully containerized for deployment**

---

## 🛠️ Tech Stack

| Layer       | Tech                            |
|-------------|----------------------------------|
| Frontend    | Streamlit + Plotly               |
| Backend     | Flask REST API                   |
| Data        | OpenWeatherMap Air Pollution API |
| ML Model    | Linear Regression (scikit-learn) |
| Deployment  | Localhost / Docker-ready         |

---

## ⚙️ Run Locally

### 1️⃣ Backend (Flask API)

```bash
cd backend
pip install -r requirements.txt
python app.py

2️⃣ Frontend (Streamlit App)
bash
Copy
Edit
cd frontend
streamlit run app.py
Make sure both are running:

Flask at: http://localhost:5000

Streamlit at: http://localhost:8501

🤖 ML Forecasting Model
Trained on simulated AQI trends using Linear Regression

Generates 7-day predictions

Easily replaceable with LSTM, XGBoost, or real datasets

🌍 API Used
OpenWeatherMap Air Pollution API

📂 Folder Structure
bash
Copy
Edit
/frontend
  └── app.py              → Streamlit frontend
/backend
  └── app.py              → Flask backend
/model
  └── aqi_predictor.pkl   → Trained ML model
aqi_log.csv               → Data logging file

🙌 Contributors
Prithish Misra

📜 License
This project is licensed under the MIT License.

