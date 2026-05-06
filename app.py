import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

# Setup the Page
st.set_page_config(page_title="Pahang Healthcare Dashboard", layout="wide")
st.title("🏥 Pahang Klinik Kesihatan & Hospital Dashboard")

# Load Upgraded Data (Now with more districts and Image URLs!)
data = {
    'Name': [
        'Hospital Tengku Ampuan Afzan (HTAA)', 
        'KK Bandar Kuantan', 
        'Hospital Sultan Haji Ahmad Shah', 
        'Hospital Pekan', 
        'Hospital Kuala Lipis'
    ],
    'District': ['Kuantan', 'Kuantan', 'Temerloh', 'Pekan', 'Lipis'],
    'Latitude': [3.8015, 3.8126, 3.4500, 3.5000, 4.1800],
    'Longitude': [103.3220, 103.3256, 102.4500, 103.3800, 102.0500],
    'Pegawai_Farmasi': [25, 5, 18, 10, 8],
    'Penolong_Pegawai': [40, 8, 30, 15, 12],
    # Adding direct links to pictures on the internet
    'Image_URL': [
        'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Hospital_Tengku_Ampuan_Afzan.jpg/300px-Hospital_Tengku_Ampuan_Afzan.jpg',
        'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=300&q=80', # Generic clinic photo
        'https://images.unsplash.com/photo-1587351021759-3e566b6af7cc?w=300&q=80', # Generic hospital photo
        'https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=300&q=80', # Generic hospital photo
        'https://images.unsplash.com/photo-1516549655169-df83a0774514?w=300&q=80'  # Generic hospital photo
    ]
}
df = pd.DataFrame(data)

# Sidebar for Distance Calculator
st.sidebar.header("📍 Distance Calculator")
facility_1 = st.sidebar.selectbox("Select First Facility", df['Name'].tolist())
facility_2 = st.sidebar.selectbox("Select Second Facility", df[df['Name'] != facility_1]['Name'].tolist())

if facility_1 and facility_2:
    coords_1 = (df[df['Name'] == facility_1]['Latitude'].values[0], df[df['Name'] == facility_1]['Longitude'].values[0])
    coords_2 = (df[df['Name'] == facility_2]['Latitude'].values[0], df[df['Name'] == facility_2]['Longitude'].values[0])
    distance = geodesic(coords_1, coords_2).kilometers
    st.sidebar.success(f"**Distance:** {distance:.2f} km")

# Create the Map (Centered on Pahang)
m = folium.Map(location=[3.75, 102.75], zoom_start=8)

# Add Markers with Pictures
for index, row in df.iterrows():
    # We use HTML here to tell the popup to load the image link
    popup_html = f"""
    <div style="width: 250px; font-family: Arial, sans-serif;">
        <h4 style="margin-top: 0;">{row['Name']}</h4>
        <img src="{row['Image_URL']}" width="100%" style="border-radius: 5px; margin-bottom: 10px;">
        <p style="margin: 2px 0;"><b>District:</b> {row['District']}</p>
        <p style="margin: 2px 0;"><b>Pegawai Farmasi:</b> {row['Pegawai_Farmasi']}</p>
        <p style="margin: 2px 0;"><b>Penolong Pegawai:</b> {row['Penolong_Pegawai']}</p>
    </div>
    """
    
    # Change icon color based on if it's a Hospital or Clinic
    icon_color = "red" if "Hospital" in row['Name'] else "blue"
    
    folium.Marker(
        [row['Latitude'], row['Longitude']],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=row['Name'],
        icon=folium.Icon(color=icon_color, icon="info-sign")
    ).add_to(m)

# Draw a line between the two selected facilities
if facility_1 and facility_2:
    folium.PolyLine([coords_1, coords_2], color="red", weight=2.5, opacity=0.8).add_to(m)

# Display Map and Data
st_folium(m, width=1000, height=500)
st.dataframe(df, use_container_width=True)