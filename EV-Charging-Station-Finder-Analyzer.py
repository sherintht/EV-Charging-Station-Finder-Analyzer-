import streamlit as st
import pandas as pd
import requests
import folium
import numpy as np
from streamlit_folium import folium_static
from geopy.distance import geodesic
from geopy.geocoders import Nominatim  # For geolocation fallback

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="EV Charging Station Finder",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. GET USER'S CURRENT LOCATION ---
st.sidebar.header("Your Location")

# Fallback function to get geolocation using geopy
def get_location():
    geolocator = Nominatim(user_agent="ev-charging-app")
    location = geolocator.geocode("Thrissur, India")  # Fallback to Thrissur
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

# Try using streamlit-geolocation to get the user's location
try:
    from streamlit_geolocation import geolocation
    location = geolocation()
    if location and location.get('latitude') and location.get('longitude'):
        latitude = location['latitude']
        longitude = location['longitude']
        st.sidebar.write(f"Your current location: Latitude: {latitude:.4f}, Longitude: {longitude:.4f}")
except ImportError:
    st.warning("streamlit-geolocation module is unavailable. Using fallback geolocation.")
    latitude, longitude = get_location()
    if latitude and longitude:
        st.sidebar.write(f"Fallback location: Latitude: {latitude:.4f}, Longitude: {longitude:.4f}")
    else:
        st.sidebar.warning("Could not determine location. Using default coordinates (Thrissur).")
        latitude = st.sidebar.number_input("Enter Latitude:", value=10.5276, min_value=-90.0, max_value=90.0, step=0.0001, format="%.4f")
        longitude = st.sidebar.number_input("Enter Longitude:", value=76.2144, min_value=-180.0, max_value=180.0, step=0.0001, format="%.4f")


# --- 3. DATA FETCHING AND CACHING ---
@st.cache_data(ttl=3600)
def get_station_data(country_code='IN', max_results=1000):
    """Fetches charging station data from Open Charge Map API and simulates extra data."""
    try:
        API_KEY = st.secrets["openchargemap"]["api_key"]
    except (FileNotFoundError, KeyError):
        st.error("OpenChargeMap API key not found. Please add it to your Streamlit secrets.")
        return pd.DataFrame()

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

        if 'StatusType' in data.columns:
            data['Is_Operational'] = data['StatusType'].apply(lambda x: x.get('IsOperational', False) if isinstance(x, dict) else False)
        else:
            data['Is_Operational'] = False

        return data
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()

# --- 4. UTILITY FUNCTION ---
def find_nearest_station(user_lat, user_lon, df):
    """Finds the nearest charging station from the user's current location."""
    if df.empty:
        return None, float('inf')
        
    min_distance = float('inf')
    nearest_station = None

    for _, row in df.iterrows():
        distance = geodesic((user_lat, user_lon), (row['Latitude'], row['Longitude'])).km
        if distance < min_distance:
            min_distance = distance
            nearest_station = row
            
    return nearest_station, min_distance

# --- 5. MAIN APP ---
st.title("EV Charging Station Finder & Analyzer ⚡")
df = get_station_data()

if not df.empty:
    # --- 6. SIDEBAR FILTERING ---
    st.sidebar.header("Filter Stations")
    cities = sorted(df['Town'].dropna().unique())
    selected_city = st.sidebar.selectbox("Select a City", ["All"] + cities)
    min_rating = st.sidebar.slider("Minimum User Rating", 1.0, 5.0, 3.5, 0.1)

    # --- 7. FILTERING LOGIC ---
    filtered_df = df.copy()
    if selected_city != "All":
        st.subheader(f"Showing Stations in: {selected_city}")
        filtered_df = filtered_df[filtered_df['Town'] == selected_city]
    else:
        st.subheader("Showing All Stations Near You")
    
    filtered_df = filtered_df[filtered_df['Avg_Rating'] >= min_rating]

    # --- 8. NEAREST STATION INFO ---
    nearest_station, distance = find_nearest_station(latitude, longitude, df)
    if nearest_station is not None:
        st.sidebar.write(f"Distance to nearest station: **{distance:.2f} km**")
        st.header(f"Nearest Station to You: {nearest_station['Title']}")
        st.write(f"**Location**: {nearest_station['Town']} | **Rating**: {nearest_station['Avg_Rating']} ⭐ | **Price**: ₹{nearest_station['Price_per_kWh']} per kWh")
    else:
        st.warning("No charging stations found in the dataset.")

    st.markdown("---")

    # --- 9. MAP LEGEND ---
    st.subheader("📍 Map Legend")
    st.markdown(
        """
        - <span style="color:blue">**🔵 Your Location**</span>
        - <span style="color:purple">**🟣 Nearest Station**</span>
        - <span style="color:orange">**🟠 Operational Station (in filtered view)**</span>
        - <span style="color:red">**🟥 Offline/Unknown Status Station (in filtered view)**</span>
        """,
        unsafe_allow_html=True
    )
    st.info("Click on a station's icon to see more details, including the distance from your location.")

    # --- 10. MAP DISPLAY ---
    if selected_city != "All" and not filtered_df.empty:
        map_center = [filtered_df['Latitude'].mean(), filtered_df['Longitude'].mean()]
        zoom_start = 13
    else:
        map_center = [latitude, longitude]
        zoom_start = 12
    
    m = folium.Map(location=map_center, zoom_start=zoom_start, tiles="CartoDB positron")

    # Marker for user's location
    folium.Marker(
        location=[latitude, longitude],
        popup="Your Location",
        icon=folium.Icon(color='blue', icon='user', prefix='fa')
    ).add_to(m)

    # Marker for the nearest charging station
    if nearest_station is not None:
        folium.Marker(
            location=[nearest_station['Latitude'], nearest_station['Longitude']],
            popup=folium.Popup(f"<b>Nearest Station:</b><br>{nearest_station['Title']}<br><b>Distance: {distance:.2f} km</b>", max_width=250),
            icon=folium.Icon(color='purple', icon='bolt', prefix='fa')
        ).add_to(m)

    # Add markers for all filtered stations
    for _, row in filtered_df.iterrows():
        # Skip the nearest station if it's already plotted
        if nearest_station is not None and row.equals(nearest_station):
            continue

        station_coords = (row['Latitude'], row['Longitude'])
        user_coords = (latitude, longitude)
        distance_to_station = geodesic(user_coords, station_coords).km
        
        # Assign color and icon based on status for filtered stations
        if row['Is_Operational']:
            color, icon = 'orange', 'bolt'
        else:
            color, icon = 'red', 'ban'  # Changed color to red for offline/unknown stations
            
        popup_html = f"""
        <h6>{row['Title']}</h6>
        <b>Distance:</b> {distance_to_station:.2f} km<br>
        <b>Status:</b> {'Operational' if row['Is_Operational'] else 'Offline'}<br>
        <b>Price:</b> ₹{row['Price_per_kWh']}/kWh (est.)<br>
        <b>Rating:</b> {row['Avg_Rating']} ★
        """
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=color, icon=icon, prefix='fa')
        ).add_to(m)

    folium_static(m, width=1200, height=600)
else:
    st.error("Failed to load station data. Please check API key or network connection."
