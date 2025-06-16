import streamlit as st
import pandas as pd
import requests
import folium
import numpy as np
from streamlit_folium import folium_static

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="EV Charging Station Finder",
    page_icon="⚡",
    layout="wide",
)

# --- 2. DATA FETCHING AND CACHING ---
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def get_station_data(country_code='IN', max_results=500):
    """Fetches charging station data from Open Charge Map API and simulates extra data."""
    API_URL = "https://api.openchargemap.io/v3/poi"
    params = {
        'output': 'json',
        'countrycode': country_code,
        'maxresults': max_results,
        'compact': True,
        'verbose': False
    }
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = pd.DataFrame(response.json())

        # --- Data Cleaning & Enrichment ---
        # Extract essential fields
        data['Latitude'] = data['AddressInfo'].apply(lambda x: x.get('Latitude'))
        data['Longitude'] = data['AddressInfo'].apply(lambda x: x.get('Longitude'))
        data['Title'] = data['AddressInfo'].apply(lambda x: x.get('Title'))
        data['Town'] = data['AddressInfo'].apply(lambda x: x.get('Town'))
        data.dropna(subset=['Latitude', 'Longitude', 'Title'], inplace=True)

        # Simulate dynamic data (pricing, ratings) for demonstration
        np.random.seed(42)  # for reproducible results
        data['Price_per_kWh'] = np.random.uniform(10, 25, len(data)).round(2)  # Simulated price in INR
        data['Avg_Rating'] = np.random.uniform(3.5, 5.0, len(data)).round(1)
        data['Is_Operational'] = data['StatusType'].apply(lambda x: x.get('IsOperational', False) if isinstance(x, dict) else False)

        return data
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()

# --- 3. MAIN APP ---
st.title("EV Charging Station Finder & Analyzer ⚡")
df = get_station_data()

if not df.empty:
    # --- 4. SIDEBAR FILTERS ---
    st.sidebar.header("Filter Stations")

    # Filter by City
    cities = sorted(df['Town'].dropna().unique())
    selected_city = st.sidebar.selectbox("Select a City", ["All"] + cities)

    # Filter by Charging Speed (using simulated PowerKW)
    speed_options = {"Any": (0, 350), "Slow (< 7kW)": (0, 7), "Fast (7-50kW)": (7, 50), "Ultra-Fast (> 50kW)": (50, 350)}
    selected_speed = st.sidebar.select_slider("Charging Speed", options=list(speed_options.keys()))

    # Filter by Rating
    min_rating = st.sidebar.slider("Minimum User Rating", 1.0, 5.0, 3.5, 0.1)

    # --- 5. FILTERING LOGIC ---
    filtered_df = df.copy()
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df['Town'] == selected_city]
    
    # Note: PowerKW is not a direct field; this simulates filtering. For a real app, parse 'Connections'.
    # This example filters based on the presence of stations, not specific power levels.
    
    filtered_df = filtered_df[filtered_df['Avg_Rating'] >= min_rating]

    # --- 6. MAP DISPLAY ---
    st.header(f"Found {len(filtered_df)} Stations")
    map_center = [filtered_df['Latitude'].mean(), filtered_df['Longitude'].mean()] if not filtered_df.empty else [20.5937, 78.9629]
    m = folium.Map(location=map_center, zoom_start=12 if selected_city != "All" else 5)

    for idx, row in filtered_df.iterrows():
        color = 'green' if row['Is_Operational'] else 'red'
        popup_html = f"""
        <h6>{row['Title']}</h6>
        <b>Status:</b> {'Operational' if row['Is_Operational'] else 'Offline'}<br>
        <b>Price:</b> ₹{row['Price_per_kWh']}/kWh (est.)<br>
        <b>Rating:</b> {row['Avg_Rating']} ★
        """
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=color, icon='flash', prefix='fa')
        ).add_to(m)

    folium_static(m, width=1200, height=600)

else:
    st.error("Failed to load station data. Please try again later.")
