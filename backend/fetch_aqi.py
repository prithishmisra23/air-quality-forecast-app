import requests

API_KEY = 'b48771cc44eb3963dc408c3759655e2a'

def get_aqi_data(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    res = requests.get(url).json()

    aqi = res['list'][0]['main']['aqi']
    components = res['list'][0]['components']

    return {
        'aqi': aqi,
        'components': components
    }
