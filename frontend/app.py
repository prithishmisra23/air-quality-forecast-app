import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Air Quality Visualizer", layout="wide")

# Title
st.title("🌍 Air Quality Visualizer and Forecast")
backend_url = "https://air-quality-backend-7ys9.onrender.com"

# Input Options
option = st.radio("Choose Input Type", ("City Name", "Latitude/Longitude"))

if option == "City Name":
    city = st.text_input("Enter your City Name", "Delhi")
    coords = None
else:
    lat = st.number_input("Enter Latitude", value=28.6139)
    lon = st.number_input("Enter Longitude", value=77.2090)
    coords = {"lat": lat, "lon": lon}
    city = None

# AQI Fetch
if st.button("🔍 Get Real-Time AQI"):
    try:
        if city:
            response = requests.get(f"{backend_url}/api/aqi", params={"city": city})
        else:
            response = requests.get(f"{backend_url}/api/aqi", params=coords)

        response.raise_for_status()
        aqi_data = response.json()

        st.subheader("📌 AQI Information")
        st.metric("AQI Value", aqi_data['aqi'])
        st.write("Pollutants Breakdown:")
        st.json(aqi_data['components'])

        # Show map
        if "lat" in aqi_data and "lon" in aqi_data:
            st.subheader("🗺️ Location")
            m = folium.Map(location=[aqi_data['lat'], aqi_data['lon']], zoom_start=10)
            folium.Marker(
                [aqi_data['lat'], aqi_data['lon']],
                tooltip="Monitoring Location",
                popup=f"AQI: {aqi_data['aqi']}"
            ).add_to(m)
            st_folium(m, width=700, height=500)

    except Exception as e:
        st.error(f"Failed to fetch AQI: {e}")

# History Graph
if st.button("📈 Show 7-day Historical AQI"):
    try:
        hist_response = requests.get(f"{backend_url}/api/history")
        hist_response.raise_for_status()
        hist_data = hist_response.json()['history']
        df = pd.DataFrame(hist_data)
        fig = px.line(df, x="date", y="aqi", title="📅 7-Day AQI History", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error fetching historical data: {e}")

# Custom Prediction
st.markdown("---")
st.header("🤖 Predict AQI with Custom Parameters")

col1, col2, col3 = st.columns(3)
with col1:
    pm25 = st.slider("PM2.5 Level", 0, 500, 60)
with col2:
    humidity = st.slider("Humidity (%)", 0, 100, 60)
with col3:
    temp = st.slider("Temperature (°C)", -10, 50, 30)

if st.button("📊 Predict AQI (AI Model)"):
    try:
        payload = {"pm2_5": pm25, "humidity": humidity, "temp": temp}
        pred_response = requests.post(f"{backend_url}/api/predict", json=payload)
        pred_response.raise_for_status()
        pred = pred_response.json()
        st.success(f"Predicted AQI: {pred['predicted_aqi']}")
    except Exception as e:
        st.error(f"Prediction failed: {e}")

st.markdown("---")
st.caption("Built with 💡 Streamlit + Flask + Scikit-learn | Powered by Open Source APIs")
