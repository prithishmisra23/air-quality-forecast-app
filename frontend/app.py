import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Air Quality Visualizer", layout="wide")

st.title("🌍 Air Quality Visualizer & Forecast App")
city = st.text_input("Enter a City Name", "Delhi")

backend_url = "https://air-quality-backend-7ys9.onrender.com"

# ---------- AQI Section ----------
if st.button("🔍 Get Real-time AQI"):
    try:
        response = requests.get(f"{backend_url}/api/aqi", params={"city": city})
        response.raise_for_status()
        data = response.json()

        st.subheader(f"📌 AQI in {city.title()}")
        st.metric("AQI Value", data['aqi'])
        st.json(data['components'])

        st.subheader("📍 Location on Map")
        map_ = folium.Map(location=[data['lat'], data['lon']], zoom_start=10)
        folium.Marker([data['lat'], data['lon']], popup=city.title(), tooltip="City").add_to(map_)
        st_folium(map_, width=700)

    except Exception as e:
        st.error(f"Failed to fetch AQI data: {e}")

# ---------- History Section ----------
if st.button("📈 Show 7-Day AQI History"):
    try:
        response = requests.get(f"{backend_url}/api/history", params={"city": city})
        response.raise_for_status()
        history_data = response.json()['history']

        df = pd.DataFrame(history_data)
        fig = px.line(df, x='date', y='aqi', markers=True, title="7-Day AQI Trend")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to load history: {e}")

# ---------- Prediction Section ----------
st.markdown("---")
st.header("🧠 Predict AQI with Your Inputs")

col1, col2, col3 = st.columns(3)
with col1:
    pm2_5 = st.slider("PM2.5 Level", 0, 500, 60)
with col2:
    humidity = st.slider("Humidity (%)", 0, 100, 70)
with col3:
    temp = st.slider("Temperature (°C)", -10, 50, 30)

if st.button("📊 Predict AQI"):
    try:
        payload = {"pm2_5": pm2_5, "humidity": humidity, "temp": temp}
        response = requests.post(f"{backend_url}/api/predict", json=payload)
        response.raise_for_status()
        prediction = response.json()

        st.success(f"✅ Predicted AQI: {prediction['predicted_aqi']}")

    except Exception as e:
        st.error(f"Prediction failed: {e}")
