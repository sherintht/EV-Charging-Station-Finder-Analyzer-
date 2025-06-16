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

# --- 2. MANUAL LOCATION INPUT ---
st.sidebar.header("Your Location")
st.sidebar.info("If automatic location detection is disabled for compatibility.
    Please enter your coordinates manually.")
st.sidebar.markdown("*(Default location is Kottayam)*")

latitude = st.sidebar.number_input("Enter Latitude:", value=9.5916, format="%.4f")
longitude = st.sidebar.number_input("Enter Longitude:", value=76.5222, format="%.4f")

st.sidebar.markdown("""
**How to find coordinates:**
1.  Go to Google Maps.
2.  Right-click on any point on the map.
3.  Click on the coordinates that appear to copy them.
""")

# --- 3. DATA FETCHING AND CACHING (MODIFIED FOR CONNECTOR DATA) ---
@st.cache_data(ttl=3600)
def get_station_data(country_code='IN', max_results=1000):
    """Fetches charging station data from Open Charge Map API, including Connection Types."""
    try:
        API_KEY = st.secrets["openchargemap"]["api_key"]
    except (FileNotFoundError, KeyError):
        st.error("OpenChargeMap API key not found. Please add it to your Streamlit secrets.")
        return pd.DataFrame()

    # We set compact=False to ensure the 'Connections' data is included in the response
    API_URL = "https://api.openchargemap.io/v3/poi"
    params = {'output': 'json', 'countrycode': country_code, 'maxresults': max_results, 'compact': False, 'verbose': False, 'key': API_KEY}
    
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = pd.DataFrame(response.json())

        # --- Data Cleaning & Enrichment ---
        data['Latitude'] = data['AddressInfo'].apply(lambda x: x.get('Latitude'))
        data['Longitude'] = data['AddressInfo'].apply(lambda x: x.get('Longitude'))
        data['Title'] = data['AddressInfo'].apply(lambda x: x.get('Title'))
        data['Town'] = data['AddressInfo'].apply(lambda x: x.get('Town'))
        data.dropna(subset=['Latitude', 'Longitude', 'Title'], inplace=True)
        
        # Add simulated data
        np.random.seed(42)
        data['Price_per_kWh'] = np.random.uniform(10, 25, len(data)).round(2)
        data['Avg_Rating'] = np.random.uniform(3.5, 5.0, len(data)).round(1)

        # Extract Operational Status
        if 'StatusType' in data.columns:
            data['Is_Operational'] = data['StatusType'].apply(lambda x: x.get('IsOperational', False) if isinstance(x, dict) else False)
        else:
            data['Is_Operational'] = False
        
        # Extract Connector Types from the 'Connections' list
        def extract_connectors(connections):
            if not isinstance(connections, list): return []
            titles = set()
            for conn in connections:
                if isinstance(conn, dict) and conn.get('ConnectionType') and conn['ConnectionType'].get('Title'):
                    titles.add(conn['ConnectionType']['Title'])
            return list(titles)
        data['ConnectorTypes'] = data['Connections'].apply(extract_connectors)

        return data
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()

# --- 4. UTILITY FUNCTION ---
def find_nearest_station(user_lat, user_lon, df):
    if df.empty: return None, float('inf')
    min_distance, nearest_station = float('inf'), None
    for _, row in df.iterrows():
        distance = geodesic((user_lat, user_lon), (row['Latitude'], row['Longitude'])).km
        if distance < min_distance:
            min_distance, nearest_station = distance, row
    return nearest_station, min_distance

# --- 5. MAIN APP ---
st.title("EV Charging Station Finder & Analyzer ⚡")
df = get_station_data()

if not df.empty:
    # --- 6. ALL FILTERS IN SIDEBAR ---
    st.sidebar.header("Filter Stations")
    
    # NEW FILTER: Operational Status
    show_operational_only = st.sidebar.toggle("Show only operational stations", value=True)
    
    # EXISTING FILTER: City
    cities = sorted(df['Town'].dropna().unique())
    selected_city = st.sidebar.selectbox("Select a City", ["All"] + cities)
    
    # EXISTING FILTER: Rating
    min_rating = st.sidebar.slider("Minimum User Rating", 1.0, 5.0, 3.5, 0.1)

    # NEW FILTER: Price Range
    min_price = df['Price_per_kWh'].min()
    max_price = df['Price_per_kWh'].max()
    selected_price_range = st.sidebar.slider("Price Range (per kWh)", min_value=min_price, max_value=max_price, value=(min_price, max_price))

    # NEW FILTER: Connector Type
    all_connectors = sorted(list(set(conn for conns_list in df['ConnectorTypes'] for conn in conns_list)))
    selected_connectors = st.sidebar.multiselect("Select Connector Types", options=all_connectors, default=[])

    # --- 7. APPLYING ALL FILTERS ---
    filtered_df = df.copy()

    # Apply Operational Status filter
    if show_operational_only:
        filtered_df = filtered_df[filtered_df['Is_Operational']]

    # Apply City filter
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df['Town'] == selected_city]
    
    # Apply Rating filter
    filtered_df = filtered_df[filtered_df['Avg_Rating'] >= min_rating]

    # Apply Price filter
    min_p, max_p = selected_price_range
    filtered_df = filtered_df[(filtered_df['Price_per_kWh'] >= min_p) & (filtered_df['Price_per_kWh'] <= max_p)]

    # Apply Connector filter
    if selected_connectors:
        filtered_df = filtered_df[filtered_df['ConnectorTypes'].apply(lambda station_conns: any(sel_conn in station_conns for sel_conn in selected_connectors))]

    # --- 8. DISPLAY RESULTS ---
    if selected_city != "All":
        st.subheader(f"Showing Stations in: {selected_city}")
    else:
        st.subheader("Showing All Stations Near You")

    # Nearest station is calculated on the unfiltered dataframe to be accurate
    nearest_station, distance = find_nearest_station(latitude, longitude, df)
    if nearest_station is not None:
        st.sidebar.write(f"Distance to nearest station: **{distance:.2f} km**")
        st.header(f"Nearest Station to You: {nearest_station['Title']}")
        st.write(f"**Location**: {nearest_station['Town']} | **Rating**: {nearest_station['Avg_Rating']} ⭐ | **Price**: ₹{nearest_station['Price_per_kWh']} per kWh")
    else:
        st.warning("No stations found in dataset.")

    st.markdown("---")
    st.subheader("📍 Map Legend")
    st.markdown("""
        - <span style="color:blue">**🔵 Your Location**</span>
        - <span style="color:purple">**🟣 Nearest Station**</span>
        - <span style="color:orange">**🟠 Operational Station (in filtered view)**</span>
        - <span style="color:red">**🔴 Offline/Unknown Status Station (in filtered view)**</span>
        """, unsafe_allow_html=True)

    # --- 9. MAP DISPLAY ---
    st.info(f"Showing {len(filtered_df)} of {len(df)} total stations based on your filters.")

    if not filtered_df.empty:
        if selected_city != "All":
            map_center = [filtered_df['Latitude'].mean(), filtered_df['Longitude'].mean()]
            zoom_start = 13
        else:
            map_center = [latitude, longitude]
            zoom_start = 12
        
        m = folium.Map(location=map_center, zoom_start=zoom_start, tiles="CartoDB positron")
        folium.Marker(location=[latitude, longitude], popup="Your Location", icon=folium.Icon(color='blue', icon='user', prefix='fa')).add_to(m)
        if nearest_station is not None:
            folium.Marker(location=[nearest_station['Latitude'], nearest_station['Longitude']], popup=folium.Popup(f"<b>Nearest Station:</b><br>{nearest_station['Title']}<br><b>Distance: {distance:.2f} km</b>", max_width=250), icon=folium.Icon(color='purple', icon='bolt', prefix='fa')).add_to(m)

        for _, row in filtered_df.iterrows():
            if nearest_station is not None and row.equals(nearest_station): continue
            distance_to_station = geodesic((latitude, longitude), (row['Latitude'], row['Longitude'])).km
            color, icon = ('orange', 'bolt') if row['Is_Operational'] else ('red', 'times-circle')
            connectors_str = ', '.join(row['ConnectorTypes'])
            popup_html = f"""<h6>{row['Title']}</h6>
                             <b>Distance:</b> {distance_to_station:.2f} km<br>
                             <b>Status:</b> {'Operational' if row['Is_Operational'] else 'Offline'}<br>
                             <b>Price:</b> ₹{row['Price_per_kWh']}/kWh (est.)<br>
                             <b>Rating:</b> {row['Avg_Rating']} ★<br>
                             <b>Connectors:</b> {connectors_str}"""
            folium.Marker(location=[row['Latitude'], row['Longitude']], popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color=color, icon=icon, prefix='fa')).add_to(m)

        folium_static(m, width=1200, height=600)
    else:
        st.warning("No stations match your current filter settings.")
else:
    st.error("Failed to load station data. Please check API key or network connection.")
