# streamlit_app.py (Streamlit Frontend)

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# Set up the Streamlit page configuration
st.set_page_config(page_title="Air Quality Visualizer", layout="wide")
st.title("🌍 Air Quality Visualizer and Forecast")

# Backend URL - IMPORTANT: Update this to your deployed Flask backend URL
# If running Flask locally, use "http://localhost:5000" or "http://127.0.0.1:5000"
backend_url = "https://air-quality-backend-7ys9.onrender.com" 

# Initialize session state variables to store data across reruns
if 'aqi_data' not in st.session_state:
    st.session_state.aqi_data = None
if 'aqi_prediction' not in st.session_state:
    st.session_state.aqi_prediction = None

# --- Current Air Quality Section ---
st.subheader("Current Air Quality")
option = st.radio("Choose Input Type", ("City Name", "Latitude/Longitude"))

city_input = None
coords_input = None

if option == "City Name":
    city_input = st.text_input("Enter your City Name", "Delhi")
else: # Latitude/Longitude selected
    # Default values set for Kanpur, Uttar Pradesh, India
    lat_input = st.number_input("Enter Latitude", value=26.4499, format="%.4f")
    lon_input = st.number_input("Enter Longitude", value=80.3312, format="%.4f")
    coords_input = {"lat": lat_input, "lon": lon_input}

# Button to fetch Real-Time AQI
if st.button("🔍 Get Real-Time AQI"):
    try:
        response = None
        if option == "City Name" and city_input:
            response = requests.get(f"{backend_url}/api/aqi", params={"city": city_input})
        elif option == "Latitude/Longitude" and coords_input:
            response = requests.get(f"{backend_url}/api/aqi", params=coords_input)
        else:
            st.warning("Please enter a city or coordinates to fetch AQI.")
            st.session_state.aqi_data = None
            response = None # No request made

        if response:
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            st.session_state.aqi_data = response.json()
    except requests.exceptions.RequestException as e:
        # Catch specific network/API errors
        st.error(f"Failed to fetch AQI (Network/API Error): {e}. Please check the backend server and URL.")
        st.session_state.aqi_data = None
    except Exception as e:
        # Catch other unexpected errors (e.g., JSON parsing issues)
        st.error(f"An unexpected error occurred while fetching AQI: {e}")
        st.session_state.aqi_data = None

# Display Real-Time AQI results if available
if st.session_state.aqi_data:
    aqi_data = st.session_state.aqi_data
    st.subheader("📌 Real-Time AQI Information")
    aqi_scale = {
    1: "Good",
    2: "Fair",
    3: "Moderate",
    4: "Poor",
    5: "Very Poor"
}
aqi_number = aqi_data.get('aqi', 'N/A')
aqi_label = aqi_scale.get(aqi_number, "Unknown")
st.metric("Current AQI Value", f"{aqi_number} ({aqi_label})")
st.write("Pollutants Breakdown (μg/m³):")
st.json(aqi_data.get('components', {})) # Use .get for safe access, provide empty dict if not found

    # Display map if coordinates are available
    if "lat" in aqi_data and "lon" in aqi_data:
        st.subheader("🗺️ Location Map")
        m = folium.Map(location=[aqi_data['lat'], aqi_data['lon']], zoom_start=10)
        folium.Marker(
            [aqi_data['lat'], aqi_data['lon']],
            tooltip="Monitoring Location",
            popup=f"AQI: {aqi_data.get('aqi', 'N/A')}"
        ).add_to(m)
        st_folium(m, width=700, height=500)

# --- Historical Air Quality Section ---
st.markdown("---")
st.subheader("Historical Air Quality")
if st.button("📈 Show 7-day Historical AQI"):
    try:
        # Determine which city to use for historical data
        # Your backend's history endpoint uses city name
        city_for_history = "Delhi" # Default if no specific city is selected
        if option == "City Name" and city_input:
            city_for_history = city_input
        # If Lat/Lon is selected, we still default to "Delhi" for history
        # as your backend's /api/history route only accepts 'city' as a parameter.
        
        hist_response = requests.get(f"{backend_url}/api/history", params={"city": city_for_history})
        hist_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        # The backend directly returns a list of dictionaries for history
        hist_data = hist_response.json()

        if hist_data: # Check if the historical data list is not empty
            df = pd.DataFrame(hist_data)
            df['date'] = pd.to_datetime(df['date']) # Convert 'date' column to datetime objects
            df = df.sort_values('date') # Sort by date for proper time series plotting
            fig = px.line(df, x="date", y="aqi", title=f"📅 7-Day AQI History for {city_for_history}", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No historical data available for {city_for_history}.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching historical data (Network/API Error): {e}. Please check the backend server and URL.")
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching historical data: {e}")


# --- AQI Prediction Section ---
st.markdown("---")
st.header("🤖 Predict AQI with Custom Parameters")

# --- FIX: Sliders for pollutant inputs adjusted to match your model's training data ---
# Your model expects: 'pm2_5', 'humidity', 'temperature'
col_pred1, col_pred2, col_pred3 = st.columns(3)
with col_pred1:
    pm2_5_val = st.slider("PM2.5 [μg/m³]", 0.0, 500.0, 60.0, step=1.0, 
                         help="Particulate Matter 2.5 micrometers or less in diameter. Typical range: 0-250 µg/m³")
with col_pred2:
    humidity_val = st.slider("Humidity (%)", 0, 100, 60, step=1, 
                             help="Relative humidity in percentage. Typical range: 0-100%")
with col_pred3:
    temperature_val = st.slider("Temperature (°C)", -10, 50, 30, step=1, 
                                help="Air temperature in Celsius. Typical range: -10 to 50°C")

# Button to trigger AQI prediction
if st.button("📊 Predict AQI (AI Model)"):
    try:
        payload = {
            "pm2_5": pm2_5_val,
            "humidity": humidity_val,
            "temperature": temperature_val
        }
        st.write("📤 Sending the following data to backend for prediction:")
        st.json(payload)

        pred_response = requests.post(f"{backend_url}/api/predict", json=payload)
        pred_response.raise_for_status()
        pred = pred_response.json()

        st.write("📥 Received response from backend:")
        st.json(pred)

        if "prediction" in pred:
            st.session_state.aqi_prediction = f"Predicted AQI: {pred['prediction']}"
        else:
            st.session_state.aqi_prediction = f"❌ Prediction key missing in response: {pred}"

    except requests.exceptions.RequestException as e:
        st.session_state.aqi_prediction = f"Prediction failed (Network/API Error): {e}. Please check backend server and URL."
    except Exception as e:
        st.session_state.aqi_prediction = f"Prediction failed (Unexpected Error): {e}"
    except requests.exceptions.RequestException as e:
        st.session_state.aqi_prediction = f"Prediction failed (Network/API Error): {e}. Please check backend server and URL."
    except Exception as e:
        st.session_state.aqi_prediction = f"Prediction failed (Unexpected Error): {e}"

# Display prediction result
if st.session_state.aqi_prediction:
    if "Predicted AQI" in st.session_state.aqi_prediction:
        st.success(st.session_state.aqi_prediction)
    else:
        st.error(st.session_state.aqi_prediction)

st.markdown("---")
st.caption("Built with 💡 Streamlit + Flask + Scikit-learn | Powered by Open Source APIs")
