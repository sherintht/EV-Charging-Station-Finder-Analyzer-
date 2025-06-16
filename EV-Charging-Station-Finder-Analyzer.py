import streamlit as st
import pandas as pd
import requests
import folium
import numpy as np
from streamlit_folium import folium_static
from geopy.distance import geodesic

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="EV Charging Station Finder",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. GET USER'S CURRENT LOCATION ---
st.sidebar.header("Enter Your Location")

# Use Streamlit's widgets or input method to get user's latitude and longitude
latitude = st.sidebar.number_input("Enter Latitude:", value=9.5918, min_value=-90.0, max_value=90.0, step=0.0001)
longitude = st.sidebar.number_input("Enter Longitude:", value=76.5225, min_value=-180.0, max_value=180.0, step=0.0001)

# --- 3. DATA FETCHING AND CACHING ---
@st.cache_data(ttl=3600)
def get_station_data(country_code='IN', max_results=500):
    """Fetches charging station data from Open Charge Map API and simulates extra data."""
    
    # Fetch API Key
    API_KEY = st.secrets["openchargemap"]["api_key"]

    API_URL = "https://api.openchargemap.io/v3/poi"
    params = {
        'output': 'json',
        'countrycode': country_code,
        'maxresults': max_results,
        'compact': True,
        'verbose': False,
        'key': API_KEY
    }
    
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = pd.DataFrame(response.json())

        # Data Cleaning & Enrichment
        data['Latitude'] = data['AddressInfo'].apply(lambda x: x.get('Latitude'))
        data['Longitude'] = data['AddressInfo'].apply(lambda x: x.get('Longitude'))
        data['Title'] = data['AddressInfo'].apply(lambda x: x.get('Title'))
        data['Town'] = data['AddressInfo'].apply(lambda x: x.get('Town'))
        data.dropna(subset=['Latitude', 'Longitude', 'Title'], inplace=True)

        np.random.seed(42)
        data['Price_per_kWh'] = np.random.uniform(10, 25, len(data)).round(2)
        data['Avg_Rating'] = np.random.uniform(3.5, 5.0, len(data)).round(1)

        # Check for StatusType
        if 'StatusType' in data.columns:
            data['Is_Operational'] = data['StatusType'].apply(lambda x: x.get('IsOperational', False) if isinstance(x, dict) else False)
        else:
            data['Is_Operational'] = False

        return data
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()

# --- 4. FIND THE NEAREST STATION BASED ON THE USER'S LOCATION ---

def find_nearest_station(user_lat, user_lon, df):
    """Finds the nearest charging station from the user's current location."""
    nearest_station = None
    min_distance = float('inf')

    for _, row in df.iterrows():
        station_coords = (row['Latitude'], row['Longitude'])
        user_coords = (user_lat, user_lon)

        # Calculate the distance using geodesic (Haversine formula)
        distance = geodesic(user_coords, station_coords).km

        if distance < min_distance:
            min_distance = distance
            nearest_station = row

    return nearest_station, min_distance

# --- 5. MAIN APP ---
st.title("EV Charging Station Finder & Analyzer ⚡")
df = get_station_data()

if not df.empty:
    # Find the nearest station to the user’s location
    nearest_station, distance = find_nearest_station(latitude, longitude, df)

    st.sidebar.write(f"Distance to nearest station: {distance:.2f} km")

    # Display the nearest station information
    st.header(f"Nearest Station: {nearest_station['Title']}")
    st.write(f"**Location**: {nearest_station['Town']}")
    st.write(f"**Rating**: {nearest_station['Avg_Rating']} ⭐")
    st.write(f"**Price**: ₹{nearest_station['Price_per_kWh']} per kWh")

    # --- MAP DISPLAY ---
    map_center = [latitude, longitude]
    m = folium.Map(location=map_center, zoom_start=12)

    # Marker for user's location
    folium.Marker(
        location=[latitude, longitude],
        popup="Your Location",
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(m)

    # Marker for the nearest charging station
    folium.Marker(
        location=[nearest_station['Latitude'], nearest_station['Longitude']],
        popup=folium.Popup(f"{nearest_station['Title']}", max_width=250),
        icon=folium.Icon(color='green', icon='flash', prefix='fa')
    ).add_to(m)

    folium_static(m, width=1200, height=600)
else:
    st.error("Failed to load station data.")
