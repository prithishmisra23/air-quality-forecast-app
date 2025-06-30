import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Air Quality Visualizer", layout="wide")

st.title("🌍 Air Quality Visualizer and Forecast")
city = st.text_input("Enter your City Name", "Delhi")

backend_url = "https://air-quality-backend-7ys9.onrender.com"

if st.button("🔍 Get AQI"):
    try:
        aqi_response = requests.get(f"{backend_url}/api/aqi", params={"city": city})
        aqi_response.raise_for_status()
        aqi_data = aqi_response.json()

        st.subheader(f"📌 AQI for {city.capitalize()}")
        st.metric("AQI Value", aqi_data['aqi'])
        st.json(aqi_data['components'])

        # Show coordinates
        lat = aqi_data['lat']
        lon = aqi_data['lon']
        st.write(f"📍 Coordinates of {city}: {lat}, {lon}")

        # Show map
        m = folium.Map(location=[lat, lon], zoom_start=10)
        folium.Marker([lat, lon], popup=city).add_to(m)
        st_folium(m, width=700, height=500)

    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        st.error(f"Request error: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")


if st.button("📈 Show 7-day Historical Data"):
    try:
        history_response = requests.get(f"{backend_url}/api/history")
        history_response.raise_for_status()
        history_data = history_response.json()['history']

        df_history = pd.DataFrame(history_data)
        fig = px.line(df_history, x="date", y="aqi", title="7-Day AQI History", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading history: {e}")

st.markdown("---")
st.header("🧠 Predict AQI with Your Own Values")

pm25 = st.slider("PM2.5 Level", 0, 500, 50)
humidity = st.slider("Humidity (%)", 0, 100, 60)
temp = st.slider("Temperature (°C)", -10, 50, 30)

if st.button("📊 Predict AQI"):
    try:
        payload = {
            "pm2_5": pm25,
            "humidity": humidity,
            "temp": temp
        }
        predict_response = requests.post(f"{backend_url}/api/predict", json=payload)
        predict_response.raise_for_status()
        prediction = predict_response.json()

        st.success(f"Predicted AQI: {prediction['predicted_aqi']}")

    except Exception as e:
        st.error(f"Prediction failed: {e}")
