# ⚡ EV Charging Station Finder & Analyzer 🚗💨

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.29-FF4B4B?style=for-the-badge&logo=streamlit)
![Folium](https://img.shields.io/badge/Folium-0.14-blueviolet?style=for-the-badge&logo=leaflet)
![Pandas](https://img.shields.io/badge/Pandas-2.0-F8E874?style=for-the-badge&logo=pandas)

A dynamic web application built with Streamlit that helps Electric Vehicle owners find the nearest charging stations, view live availability, and filter results based on their needs.

---

## 🚀 Live Demo

**[<-- Click Here to Access the Live Application -->]**[ *(Link this to your deployed Streamlit Cloud URL)*](https://ev-charging-station-finder-analyzer.streamlit.app/)

---

## 🌟 Project Overview

The global shift to electric mobility has created a critical need for accessible and reliable charging infrastructure. This project tackles that challenge head-on by providing a user-friendly platform to locate and analyze EV charging stations. It's more than just a map—it's a smart tool designed to reduce "range anxiety" and streamline the charging experience for EV drivers.

This application demonstrates proficiency in **API integration**, **geospatial data processing**, and building **interactive, data-driven UIs**.

---

## ✨ Key Features

* **📍 Nearest Station Finder**: Automatically calculates and highlights the closest charging station based on the user's real-time or manually entered geographic coordinates (latitude/longitude).
* **🗺️ Interactive Map Display**: Utilizes **Folium** to render an interactive map showing the user's location and all nearby charging stations.
* **🟢 Live Station Status**: Color-coded markers instantly show whether a station is **Operational** (green) or **Offline** (red), using real-time data from the Open Charge Map API.
* **🔍 Dynamic Filtering**: Users can easily filter the displayed stations by:
    * **City**: Narrow down the search to a specific urban area.
    * **Charging Speed**: Select from Slow, Fast, or Ultra-Fast chargers.
    * **User Rating**: Display only stations that meet a minimum average user rating.
* **ℹ️ Rich Station Data**: Clicking on any station reveals a popup with essential details, including:
    * Station Name & Address
    * Operational Status
    * Simulated Price per kWh
    * Average User Rating

---

## 🛠️ Tech Stack & Tools

* **Frontend**: **Streamlit** (For building the interactive web UI with pure Python)
* **Geospatial Visualization**: **Folium** (A powerful Python library for creating interactive Leaflet.js maps)
* **Data Manipulation**: **Pandas** & **NumPy** (For cleaning, processing, and enriching the API data)
* **API Integration**: **Requests** (For fetching real-time data from the Open Charge Map public API)
* **Geolocation Calculations**: **Geopy** (For accurately calculating the distance between the user and stations)
* **Deployment**: **Streamlit Community Cloud**

---

## ⚙️ How It Works

1.  **User Input**: The application takes the user's latitude and longitude as input via sidebar controls.
2.  **API Data Fetching**: It sends a request to the **Open Charge Map API** to get a list of charging stations for a specified country (India).
3.  **Data Processing**: The raw JSON response is cleaned, structured into a Pandas DataFrame, and enriched with simulated data like pricing and ratings to demonstrate full functionality.
4.  **Nearest Station Calculation**: The `geopy` library calculates the geodesic distance from the user to every station, identifying the closest one.
5.  **Dynamic Rendering**: The Streamlit frontend dynamically updates the map and information cards based on user filter selections, providing a seamless and responsive experience.

---

## 🔧 Setup & Local Installation

To run this project on your local machine, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Set up your API Key:**
    * Create a `.streamlit/secrets.toml` file.
    * Add your Open Charge Map API key inside:
        ```toml
        [openchargemap]
        api_key = "YOUR_API_KEY_HERE"
        ```

4.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```

---

## 📈 Future Enhancements

* **Route Planning**: Integrate with a Directions API to plan routes with optimal charging stops.
* **User Reviews & Ratings**: Implement a database (like Firebase or SQLite) to allow users to submit their own reviews.
* **Real-Time Price Integration**: Connect to charging network APIs that provide live pricing data.
* **User Authentication**: Add user accounts to save favorite locations and vehicle types.
