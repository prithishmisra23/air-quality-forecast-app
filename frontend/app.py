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
# IMPORTANT: Ensure this URL is correct for your deployed Flask app.
# If running locally, it would be "http://localhost:5000" or "http://127.0.0.1:5000"
backend_url = "https://air-quality-backend-7ys9.onrender.com"

# Initialize session state
if 'aqi_data' not in st.session_state:
    st.session_state.aqi_data = None
if 'aqi_prediction' not in st.session_state:
    st.session_state.aqi_prediction = None

# Input selection for Real-Time AQI
st.subheader("Current Air Quality")
option = st.radio("Choose Input Type", ("City Name", "Latitude/Longitude"))

city_input = None # Initialize city_input
coords_input = None # Initialize coords_input

if option == "City Name":
    city_input = st.text_input("Enter your City Name", "Delhi")
    
else: # Latitude/Longitude
    # Set default values for Kanpur, Uttar Pradesh, India
    lat_input = st.number_input("Enter Latitude", value=26.4499) # Approx. Kanpur lat
    lon_input = st.number_input("Enter Longitude", value=80.3312) # Approx. Kanpur lon
    coords_input = {"lat": lat_input, "lon": lon_input}


# Fetch AQI data
if st.button("🔍 Get Real-Time AQI"):
    try:
        response = None # Initialize response
        if option == "City Name" and city_input:
            response = requests.get(f"{backend_url}/api/aqi", params={"city": city_input})
        elif option == "Latitude/Longitude" and coords_input:
            response = requests.get(f"{backend_url}/api/aqi", params=coords_input)
        else:
            st.warning("Please enter a city or coordinates.")
            st.session_state.aqi_data = None
            response = None # No request made, clear response

        if response:
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            st.session_state.aqi_data = response.json()
    except requests.exceptions.RequestException as e: # Catch specific request errors
        st.error(f"Failed to fetch AQI (Network/API Error): {e}. Check backend server and URL.")
        st.session_state.aqi_data = None
    except Exception as e: # Catch other potential errors (e.g., JSON parsing)
        st.error(f"An unexpected error occurred while fetching AQI: {e}")
        st.session_state.aqi_data = None


# Display AQI results if available
if st.session_state.aqi_data:
    aqi_data = st.session_state.aqi_data
    st.subheader("📌 Real-Time AQI Information")
    st.metric("Current AQI Value", aqi_data.get('aqi', 'N/A')) # Use .get for safety
    st.write("Pollutants Breakdown (μg/m³):")
    st.json(aqi_data.get('components', {})) # Use .get for safety

    if "lat" in aqi_data and "lon" in aqi_data:
        st.subheader("🗺️ Location Map")
        m = folium.Map(location=[aqi_data['lat'], aqi_data['lon']], zoom_start=10)
        folium.Marker(
            [aqi_data['lat'], aqi_data['lon']],
            tooltip="Monitoring Location",
            popup=f"AQI: {aqi_data.get('aqi', 'N/A')}"
        ).add_to(m)
        st_folium(m, width=700, height=500)

# Show historical AQI graph
st.markdown("---")
st.subheader("Historical Air Quality")
if st.button("📈 Show 7-day Historical AQI"):
    try:
        # Determine which city to use for history based on current input
        city_for_history = "Delhi" # Default if nothing is selected or entered
        if option == "City Name" and city_input:
            city_for_history = city_input
        # If Lat/Lon is selected, we still need a city name for history in your backend
        # Your backend uses Nominatim on city name for history
        # So for Lat/Lon mode, it will just use 'Delhi'
        # If you want to use the geolocated city name, you'd need to store it
        # from the /api/aqi call, or perform another reverse geocode.
        
        hist_response = requests.get(f"{backend_url}/api/history", params={"city": city_for_history})
        hist_response.raise_for_status()
        
        # --- FIX FOR ERROR 1 ---
        # The backend directly returns the list, not wrapped in a 'history' key
        hist_data = hist_response.json()
        # --- END FIX ---

        if hist_data: # Check if list is not empty
            df = pd.DataFrame(hist_data)
            df['date'] = pd.to_datetime(df['date']) # Ensure date is datetime for sorting/plotting
            df = df.sort_values('date') # Sort by date for proper time series plot
            fig = px.line(df, x="date", y="aqi", title=f"📅 7-Day AQI History for {city_for_history}", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No historical data available for {city_for_history}.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching historical data (Network/API Error): {e}. Check backend server and URL.")
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching historical data: {e}")


# AQI Prediction Section
st.markdown("---")
st.header("🤖 Predict AQI with Custom Parameters")

# --- FIX FOR ERROR 2: Add all required input fields and align with backend model expectations ---
# Ensure these sliders provide all the inputs your model expects (pm25, pm10, no2, so2, co, o3)
# Based on your backend, 'no' and 'nh3' are NOT used by the model currently.
col_pred1, col_pred2, col_pred3 = st.columns(3)
with col_pred1:
    co_val = st.slider("Carbon Monoxide (CO) [μg/m³]", 0.0, 20000.0, 500.0, step=10.0, help="Typical range: 0-10000 µg/m³")
    no2_val = st.slider("Nitrogen Dioxide (NO2) [μg/m³]", 0.0, 200.0, 50.0, step=1.0, help="Typical range: 0-100 µg/m³")
with col_pred2:
    o3_val = st.slider("Ozone (O3) [μg/m³]", 0.0, 200.0, 80.0, step=1.0, help="Typical range: 0-150 µg/m³")
    so2_val = st.slider("Sulfur Dioxide (SO2) [μg/m³]", 0.0, 100.0, 20.0, step=1.0, help="Typical range: 0-50 µg/m³")
with col_pred3:
    pm25_val = st.slider("PM2.5 [μg/m³]", 0.0, 500.0, 60.0, step=1.0, help="Typical range: 0-250 µg/m³") 
    pm10_val = st.slider("PM10 [μg/m³]", 0.0, 1000.0, 100.0, step=1.0, help="Typical range: 0-500 µg/m³")

# If your model needs 'no' and 'nh3', add them to the payload below and to backend's required_features.
# For now, excluding them as your backend's DataFrame creation does not include them.

if st.button("📊 Predict AQI (AI Model)"):
    try:
        # --- FIX FOR ERROR 2: Ensure payload matches backend's expected features and keys ---
        payload = {
            "pm25": pm25_val,
            "pm10": pm10_val,
            "no2": no2_val,
            "so2": so2_val,
            "co": co_val,
            "o3": o3_val
            # Do NOT include 'no' or 'nh3' unless your backend model explicitly uses them.
        }
        # --- END FIX ---

        pred_response = requests.post(f"{backend_url}/api/predict", json=payload)
        pred_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        pred = pred_response.json()
        
        # --- FIX FOR ERROR 2: Correctly access the prediction key from backend response ---
        # Backend returns {"prediction": value}
        st.session_state.aqi_prediction = f"Predicted AQI: {pred.get('prediction', 'N/A')}"
        # --- END FIX ---

    except requests.exceptions.RequestException as e: # Catch specific request errors
        st.session_state.aqi_prediction = f"Prediction failed (Network/API Error): {e}. Check backend server and URL."
    except Exception as e: # Catch other potential errors (e.g., JSON parsing)
        st.session_state.aqi_prediction = f"Prediction failed (Unexpected Error): {e}"

if st.session_state.aqi_prediction:
    if "Predicted AQI" in st.session_state.aqi_prediction:
        st.success(st.session_state.aqi_prediction)
    else:
        st.error(st.session_state.aqi_prediction)

st.markdown("---")
st.caption("Built with 💡 Streamlit + Flask + Scikit-learn | Powered by Open Source APIs")
