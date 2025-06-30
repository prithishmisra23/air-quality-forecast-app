import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# Set up the Streamlit page
st.set_page_config(page_title="Air Quality Visualizer", layout="wide")
st.title("🌍 Air Quality Visualizer and Forecast")

# Backend URL
backend_url = "https://air-quality-backend-7ys9.onrender.com" # Ensure this is correct

# Initialize session state
if 'aqi_data' not in st.session_state:
    st.session_state.aqi_data = None
if 'aqi_prediction' not in st.session_state:
    st.session_state.aqi_prediction = None

# Input selection for Real-Time AQI
st.subheader("Current Air Quality")
option = st.radio("Choose Input Type", ("City Name", "Latitude/Longitude"))

if option == "City Name":
    city = st.text_input("Enter your City Name", "Delhi")
    coords = None
else:
    # Set default values for Kanpur, Uttar Pradesh, India
    lat = st.number_input("Enter Latitude", value=26.4499) # Approx. Kanpur lat
    lon = st.number_input("Enter Longitude", value=80.3312) # Approx. Kanpur lon
    coords = {"lat": lat, "lon": lon}
    city = None

# Fetch AQI data
if st.button("🔍 Get Real-Time AQI"):
    try:
        if city:
            response = requests.get(f"{backend_url}/api/aqi", params={"city": city})
        else:
            response = requests.get(f"{backend_url}/api/aqi", params=coords)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        st.session_state.aqi_data = response.json()
    except requests.exceptions.RequestException as e: # Catch specific request errors
        st.error(f"Failed to fetch AQI (Network/API Error): {e}")
        st.session_state.aqi_data = None
    except Exception as e: # Catch other potential errors (e.g., JSON parsing)
        st.error(f"An unexpected error occurred while fetching AQI: {e}")
        st.session_state.aqi_data = None


# Display AQI results if available
if st.session_state.aqi_data:
    aqi_data = st.session_state.aqi_data
    st.subheader("📌 Real-Time AQI Information")
    st.metric("Current AQI Value", aqi_data['aqi'])
    st.write("Pollutants Breakdown (μg/m³):")
    st.json(aqi_data['components']) # This will show the raw JSON, good for debugging

    if "lat" in aqi_data and "lon" in aqi_data:
        st.subheader("🗺️ Location Map")
        m = folium.Map(location=[aqi_data['lat'], aqi_data['lon']], zoom_start=10)
        folium.Marker(
            [aqi_data['lat'], aqi_data['lon']],
            tooltip="Monitoring Location",
            popup=f"AQI: {aqi_data['aqi']}"
        ).add_to(m)
        st_folium(m, width=700, height=500)

# Show historical AQI graph
st.markdown("---")
st.subheader("Historical Air Quality")
if st.button("📈 Show 7-day Historical AQI"):
    try:
        # For history, you were using 'Delhi' by default in backend. If you want
        # to pass the current selected city from frontend, you'd add:
        # params={"city": city if city else "Delhi"}
        hist_response = requests.get(f"{backend_url}/api/history", params={"city": city if city else "Delhi"})
        hist_response.raise_for_status()
        
        # --- FIX FOR ERROR 1 ---
        hist_data = hist_response.json() # Corrected: No ['history'] key
        # --- END FIX ---

        if hist_data: # Check if list is not empty
            df = pd.DataFrame(hist_data)
            df['date'] = pd.to_datetime(df['date']) # Ensure date is datetime for sorting/plotting
            df = df.sort_values('date') # Sort by date for proper time series plot
            fig = px.line(df, x="date", y="aqi", title="📅 7-Day AQI History", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No historical data available for the selected city.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching historical data (Network/API Error): {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching historical data: {e}")


# AQI Prediction Section
st.markdown("---")
st.header("🤖 Predict AQI with Custom Parameters")

# --- FIX FOR ERROR 2: Add all required input fields ---
# You can adjust min/max/default values based on typical ranges for these pollutants
# Values are in µg/m³ for most, CO in mg/m³ for OpenWeatherMap, but model inputs vary
col_pred1, col_pred2, col_pred3 = st.columns(3)
with col_pred1:
    co_val = st.slider("Carbon Monoxide (CO)", 0.0, 20000.0, 500.0, step=10.0)
    no_val = st.slider("Nitrogen Monoxide (NO)", 0.0, 100.0, 10.0, step=1.0)
    no2_val = st.slider("Nitrogen Dioxide (NO2)", 0.0, 200.0, 50.0, step=1.0)
with col_pred2:
    o3_val = st.slider("Ozone (O3)", 0.0, 200.0, 80.0, step=1.0)
    so2_val = st.slider("Sulfur Dioxide (SO2)", 0.0, 100.0, 20.0, step=1.0)
    pm25_val = st.slider("PM2.5", 0.0, 500.0, 60.0, step=1.0) # This was already there
with col_pred3:
    pm10_val = st.slider("PM10", 0.0, 1000.0, 100.0, step=1.0)
    nh3_val = st.slider("Ammonia (NH3)", 0.0, 200.0, 10.0, step=1.0)
# Note: humidity and temp are NOT part of your backend's required_fields for prediction
# If your model needs them, you'd need to update your backend's required_fields as well.
# For now, remove them from the prediction payload
# humidity = st.slider("Humidity (%)", 0, 100, 60)
# temp = st.slider("Temperature (°C)", -10, 50, 30)

if st.button("📊 Predict AQI (AI Model)"):
    try:
        # --- FIX FOR ERROR 2: Include all required fields in payload ---
        payload = {
            "co": co_val,
            "no": no_val,
            "no2": no2_val,
            "o3": o3_val,
            "so2": so2_val,
            "pm2_5": pm25_val, # Use the corrected variable name
            "pm10": pm10_val,
            "nh3": nh3_val
            # Do NOT include humidity or temp unless your model and backend are updated for them
        }
        # --- END FIX ---

        pred_response = requests.post(f"{backend_url}/api/predict", json=payload)
        pred_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        pred = pred_response.json()
        st.session_state.aqi_prediction = f"Predicted AQI: {pred['predicted_aqi']}"
    except requests.exceptions.RequestException as e: # Catch specific request errors
        st.session_state.aqi_prediction = f"Prediction failed (Network/API Error): {e}"
    except Exception as e: # Catch other potential errors (e.g., JSON parsing)
        st.session_state.aqi_prediction = f"Prediction failed (Unexpected Error): {e}"

if st.session_state.aqi_prediction:
    if "Predicted AQI" in st.session_state.aqi_prediction:
        st.success(st.session_state.aqi_prediction)
    else:
        st.error(st.session_state.aqi_prediction)

st.markdown("---")
st.caption("Built with 💡 Streamlit + Flask + Scikit-learn | Powered by Open Source APIs")
