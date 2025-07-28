import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
from datetime import datetime

# Load data
df = pd.read_csv("WHH Dashboard 7-28.csv")

# Preprocessing
df['City'] = df['Welcome Happy Hour 2025 - City Name'].str.extract(r'- (.*)')
df['State'] = df['Welcome Happy Hour 2025 - City Name'].str.extract(r'(\w{2}) -')
df['Attending'] = pd.to_numeric(df['Welcome Happy Hour 2025 - Number Attending'], errors='coerce')
df['Last Updated'] = pd.to_datetime(df['Last Updated'])

# Aggregated data by city
city_summary = df.groupby(['State', 'City']).agg({'Attending':'sum'}).reset_index()
city_summary['location'] = city_summary['City'] + ", " + city_summary['State']

# Get lat/lon via geopy or fallback
@st.cache_data
def get_geolocations(locations):
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
    geolocator = Nominatim(user_agent="whh_dashboard")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    latitudes, longitudes = [], []
    for loc in locations:
        try:
            location = geocode(loc)
            if location:
                latitudes.append(location.latitude)
                longitudes.append(location.longitude)
            else:
                latitudes.append(None)
                longitudes.append(None)
        except:
            latitudes.append(None)
            longitudes.append(None)
    return latitudes, longitudes

if 'Latitude' not in city_summary.columns:
    lats, lons = get_geolocations(city_summary['location'])
    city_summary['Latitude'] = lats
    city_summary['Longitude'] = lons

# Trend data
date_summary = df.groupby(df['Last Updated'].dt.date)['Attending'].sum().reset_index()

# Streamlit layout
st.set_page_config(page_title="Welcome Happy Hour Dashboard", layout="wide")

# Custom CSS for dark purple background and centered logo
st.markdown("""
    <style>
    .main {
        background-color: #4d1979;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 2rem;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

# Centered Logo
st.image("tcu_logo.png", width=150)

st.title("Welcome Happy Hour 2025 Dashboard")

# Show total attendees
total_attendees = df['Attending'].sum()
st.metric(label="Total Registered Attendees", value=int(total_attendees))

# City Table
st.subheader("Attendees by City")
st.dataframe(
    city_summary[['City', 'State', 'Attending']]
    .sort_values(by='Attending', ascending=False)
    .reset_index(drop=True),
    use_container_width=True,
    hide_index=True
)

# US Heat Map with bigger bubbles
st.subheader("US Heat Map of Attendance")
map_data = city_summary.dropna(subset=['Latitude', 'Longitude'])
map_fig = px.scatter_geo(
    map_data,
    lat='Latitude',
    lon='Longitude',
    scope="usa",
    size='Attending',
    hover_name='location',
    title="Attendance by City",
    projection="albers usa",
    template="plotly_white"
)
map_fig.update_traces(
    marker=dict(sizemode='area', sizeref=0.2, sizemin=4),
    hovertemplate='<b>%{hovertext}</b><br>Attending: %{marker.size}<extra></extra>'
)
st.plotly_chart(map_fig, use_container_width=True)

# Trend Line
st.subheader("Attendance Over Time")
fig = px.line(date_summary, x='Last Updated', y='Attending', markers=True, title="Attendance Trend")
st.plotly_chart(fig, use_container_width=True)
