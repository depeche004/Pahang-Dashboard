import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

# --- FUNGSI LALUAN JALAN RAYA (OSRM API) ---
def get_driving_route(coord1, coord2):
    # OSRM memerlukan format (Longitude, Latitude)
    lon1, lat1 = coord1[1], coord1[0]
    lon2, lat2 = coord2[1], coord2[0]
    
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 'Ok':
                # Jarak dikembalikan dalam meter, tukar ke kilometer
                distance_km = data['routes'][0]['distance'] / 1000
                
                # Dapatkan koordinat laluan jalan raya
                route_coords = data['routes'][0]['geometry']['coordinates']
                # Folium perlukan (Latitude, Longitude), jadi kita terbalikkan susunan
                folium_route = [[coord[1], coord[0]] for coord in route_coords]
                
                return distance_km, folium_route
    except Exception as e:
        pass
    
    return None, None

# 1. TETAPAN HALAMAN
st.set_page_config(page_title="Papan Pemuka Farmasi Pahang", layout="wide")
st.title("🏥 Papan Pemuka Fasiliti Farmasi JKN Pahang")

# 2. MUAT TURUN DATA SEBENAR
try:
    df = pd.read_csv("Pahang_Healthcare_Facilities_Data_Updated.csv")
except FileNotFoundError:
    st.error("⚠️ Fail 'Pahang_Healthcare_Facilities_Data_Updated.csv' tidak dijumpai. Sila pastikan ia berada dalam folder yang sama.")
    st.stop()

# Kemas kini format nombor (tukar data kosong kepada 0)
df['Pegawai_Farmasi'] = df['Pegawai_Farmasi'].fillna(0).astype(int)
df['Penolong_Pegawai'] = df['Penolong_Pegawai'].fillna(0).astype(int)

# 3. SIDEBAR: TAPISAN DAERAH
st.sidebar.header("🔍 Tapis Ikut Daerah")
all_districts = sorted(df['District'].dropna().unique().tolist())
selected_districts = st.sidebar.multiselect("Pilih Daerah:", all_districts, default=all_districts)

filtered_df = df[df['District'].isin(selected_districts)]

# 4. SIDEBAR: KIRA JARAK PEMANDUAN
st.sidebar.header("🚗 Kira Jarak Pemanduan")
facility_1 = st.sidebar.selectbox("Fasiliti Mula", filtered_df['Name'].tolist())

fac_2_options = filtered_df[filtered_df['Name'] != facility_1]['Name'].tolist()
facility_2 = st.sidebar.selectbox("Fasiliti Destinasi", fac_2_options)

distance_km = None
route_line = None

if facility_1 and facility_2:
    coords_1 = (filtered_df[filtered_df['Name'] == facility_1]['Latitude'].values[0], filtered_df[filtered_df['Name'] == facility_1]['Longitude'].values[0])
    coords_2 = (filtered_df[filtered_df['Name'] == facility_2]['Latitude'].values[0], filtered_df[filtered_df['Name'] == facility_2]['Longitude'].values[0])
    
    with st.sidebar:
        with st.spinner("Sedang mengira laluan jalan raya..."):
            distance_km, route_line = get_driving_route(coords_1, coords_2)
            
    if distance_km is not None:
        st.sidebar.success(f"**Jarak Pemanduan:** {distance_km:.2f} km")
    else:
        st.sidebar.error("Ralat mendapatkan laluan jalan raya. Sila cuba sebentar lagi.")

# 5. BINA PETA (Fokus Semenanjung/Pahang sahaja)
m = folium.Map(location=[3.75, 102.75], zoom_start=8, min_zoom=7)

# Masukkan marker (pin) ke dalam peta
for index, row in filtered_df.iterrows():
    popup_html = f"""
    <div style="width: 220px; font-family: Arial, sans-serif;">
        <h4 style="margin-top: 0; margin-bottom: 5px; color: #2C3E50;">{row['Name']}</h4>
        <p style="margin: 2px 0; font-size: 12px; color: gray;"><b>Daerah:</b> {row['District']}</p>
        <hr style="margin: 5px 0;">
        <p style="margin: 2px 0;"><b>Pegawai Farmasi (PF):</b> {row['Pegawai_Farmasi']}</p>
        <p style="margin: 2px 0;"><b>Penolong Pegawai (PPF):</b> {row['Penolong_Pegawai']}</p>
    </div>
    """
    
    is_main_hub = "Hospital" in str(row['Name']) or "Bahagian" in str(row['Name'])
    icon_color = "red" if is_main_hub else "blue"
    
    folium.Marker(
        [row['Latitude'], row['Longitude']],
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=row['Name'],
        icon=folium.Icon(color=icon_color, icon="info-sign")
    ).add_to(m)

# Lukis garisan LALUAN JALAN RAYA jika jarak berjaya dikira
if route_line:
    # Garis tebal bewarna ungu untuk menonjolkan laluan pemanduan
    folium.PolyLine(route_line, color="#8E44AD", weight=5, opacity=0.8, tooltip=f"Jarak: {distance_km:.2f} km").add_to(m)

# FOKUS PETA (AUTO-FIT)
if not filtered_df.empty:
    # Jika laluan dipilih, fokus peta pada laluan itu. Jika tidak, fokus pada semua pin.
    if route_line:
        m.fit_bounds([[min(p[0] for p in route_line), min(p[1] for p in route_line)], 
                      [max(p[0] for p in route_line), max(p[1] for p in route_line)]])
    else:
        sw = filtered_df[['Latitude', 'Longitude']].min().values.tolist()
        ne = filtered_df[['Latitude', 'Longitude']].max().values.tolist()
        m.fit_bounds([sw, ne])

# 6. PAPARKAN PETA & JADUAL
st_folium(m, width=1000, height=550)

st.subheader(f"Senarai Fasiliti ({len(filtered_df)} dijumpai)")
clean_table = filtered_df[['Name', 'District', 'Pegawai_Farmasi', 'Penolong_Pegawai']]
st.dataframe(clean_table, use_container_width=True)