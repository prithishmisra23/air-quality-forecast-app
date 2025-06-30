import plotly.graph_objects as go
import os
import requests
import streamlit as st
import requests
import joblib
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# Predefined cities with coordinates
PRESET_CITIES = {
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639)
}

# Load ML model
model = joblib.load('model.pkl')

# Predefined city options
cities = {
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Chennai": (13.0827, 80.2707),
    "Bengaluru": (12.9716, 77.5946),
    "Kolkata": (22.5726, 88.3639),
    "Hyderabad": (17.3850, 78.4867),
    "Ahmedabad": (23.0225, 72.5714),
    "Pune": (18.5204, 73.8567),
    "Lucknow": (26.8467, 80.9462),
    "Jaipur": (26.9124, 75.7873)
}

st.title("🌍 Real-Time Air Quality & Forecast App")



# Default values (Delhi)
default_lat = 28.6139
default_lon = 77.2090
lat, lon = default_lat, default_lon
city = "Delhi"

st.markdown("## 📍 Select location")

location_mode = st.radio(
    "Choose location input mode:",
    ["Select city", "Enter coordinates manually", "Search city name"]
)

if location_mode == "Select city":
    city = st.selectbox("Select a city:", list(PRESET_CITIES.keys()))
    lat, lon = PRESET_CITIES[city]
    st.success(f"Selected city: {city} ({lat}, {lon})")

elif location_mode == "Enter coordinates manually":
    lat = st.number_input("Latitude", format="%.6f")
    lon = st.number_input("Longitude", format="%.6f")
    city = "Custom Location"
    st.success(f"Custom coordinates: {lat}, {lon}")

elif location_mode == "Search city name":
    city_name_input = st.text_input("Enter city name:")
    if st.button("Search Location"):
        geo_res = requests.get(
            f"https://nominatim.openstreetmap.org/search?city={city_name_input}&format=json"
        )
        if geo_res.status_code == 200 and geo_res.json():
            geo_data = geo_res.json()[0]
            lat = float(geo_data['lat'])
            lon = float(geo_data['lon'])
            city = city_name_input.title()
            st.success(f"Location found: {city} ({lat}, {lon})")
        else:
            st.error("City not found. Try again.")


# Display selected coordinates
st.write(f"📍 Coordinates of {city}: {lat}, {lon}")

# Show location on map
m = folium.Map(location=[lat, lon], zoom_start=10)
folium.Marker([lat, lon], popup=city).add_to(m)

st_folium(m, width=700, height=500)

if st.button("📡 Fetch AQI & Forecast"):
    try:
        # Ensure lat/lon are valid floats
try:
    lat = float(lat)
    lon = float(lon)
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Invalid latitude or longitude")

    res = requests.get(f"https://air-quality-backend-7ys9.onrender.com/api/aqi?lat={lat}&lon={lon}")
    res.raise_for_status()
    data = res.json()

    st.subheader("✅ Current AQI")
    st.metric("AQI", data['aqi'])
    
    # [Continue rest of your logic...]
    
    except ValueError as ve:
    st.error(f"Invalid coordinates: {ve}")
    except requests.exceptions.HTTPError as http_err:
    st.error(f"HTTP Error: {http_err}")
    except Exception as e:
    st.error(f"Error fetching data: {e}")

        res.raise_for_status()
        data = res.json()

        st.subheader("✅ Current AQI")
        st.metric("AQI", data['aqi'])

        st.write("🧪 Pollutants:")
        st.json(data['components'])

        st.subheader("📈 Forecasted AQI (Next Hour)")
        st.subheader("🌡️ Enter Weather Info (Optional)")
        temp = st.number_input("Temperature (°C)", min_value=-10.0, max_value=50.0, value=30.0, help="Enter temperature or leave default")
        humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=50.0, help="Enter humidity or leave default")


        input_data = [[humidity, temp, data['components']['pm2_5']]]


        prediction = model.predict(input_data)[0]
        st.success(f"Forecasted AQI: {int(prediction)}")

        # Save to CSV
        record = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "City": city,
            "Latitude": lat,
            "Longitude": lon,
            "AQI": data['aqi'],
            "PM2.5": data['components']['pm2_5'],
            "PM10": data['components'].get('pm10', 'NA'),
            "CO": data['components'].get('co', 'NA'),
            "Forecasted_AQI": int(prediction)
        }

        df = pd.DataFrame([record])
        header_needed = not os.path.exists("aqi_log.csv")
        df.to_csv("aqi_log.csv", mode='a', header=header_needed, index=False)


        # st.success("📁 Data saved to aqi_log.csv")

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        import plotly.graph_objects as go

st.subheader("📉 Past 7 Days AQI Trend")

history_res = requests.get(f"https://air-quality-backend-7ys9.onrender.com/api/history?lat={lat:.4f}&lon={lon:.4f}")
history_data = history_res.json()["history"]

dates = [item['date'] for item in history_data]
aqi_values = [item['aqi'] for item in history_data]

fig = go.Figure()
fig.add_trace(go.Scatter(x=dates, y=aqi_values, mode='lines+markers', name='AQI'))

fig.update_layout(
    title='AQI Over the Last 7 Days',
    xaxis_title='Date',
    yaxis_title='AQI Level',
    template='plotly_dark'
)

st.plotly_chart(fig)
if os.path.exists("aqi_log.csv"):
    with open("aqi_log.csv", "rb") as f:
        st.download_button("📥 Download AQI Log CSV", f, file_name="aqi_log.csv")


