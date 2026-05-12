import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

# --- FUNGSI LALUAN JALAN RAYA (OSRM API) ---
def get_driving_route(coord1, coord2):
    lon1, lat1 = coord1[1], coord1[0]
    lon2, lat2 = coord2[1], coord2[0]
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 'Ok':
                distance_km = data['routes'][0]['distance'] / 1000
                route_coords = data['routes'][0]['geometry']['coordinates']
                folium_route = [[coord[1], coord[0]] for coord in route_coords]
                return distance_km, folium_route
    except Exception as e:
        pass
    return None, None

# 1. TETAPAN HALAMAN & UI/UX (Banner KKM)
st.set_page_config(page_title="Taburan Anggota Farmasi Negeri Pahang", layout="wide")

st.markdown("""
    <div style='display: flex; align-items: center; background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
        <img src='https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Ministry_of_Health_Malaysia.svg/512px-Ministry_of_Health_Malaysia.svg.png' width='80' style='margin-right: 20px;'>
        <div>
            <h2 style='margin: 0; color: #2c3e50;'>Taburan Anggota Farmasi Negeri Pahang</h2>
            <p style='margin: 0; font-size: 16px; color: #7f8c8d;'>Sistem Analitik Taburan Sumber Manusia & Logistik Perkhidmatan Farmasi</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# 2. MUAT TURUN DATA
try:
    df = pd.read_csv("Pahang_Healthcare_Facilities_Data_Updated.csv")
except FileNotFoundError:
    st.error("⚠️ Fail data tidak dijumpai. Sila pastikan fail CSV telah dimuat naik ke GitHub.")
    st.stop()

# Kemas kini format data staf
df['Pegawai_Farmasi'] = df['Pegawai_Farmasi'].fillna(0).astype(int)
df['Penolong_Pegawai'] = df['Penolong_Pegawai'].fillna(0).astype(int)

# Persediaan lajur Populasi (Jika ada)
if 'Populasi' not in df.columns: 
    df['Populasi'] = 0
df['Populasi'] = pd.to_numeric(df['Populasi'], errors='coerce').fillna(0).astype(int)

# 3. SIDEBAR (Penapis & Routing)
st.sidebar.markdown("### 🔍 Tapis Data")
all_districts = sorted(df['District'].dropna().unique().tolist())
selected_districts = st.sidebar.multiselect("Pilih Daerah:", all_districts, default=all_districts)

filtered_df = df[df['District'].isin(selected_districts)]

# Expander untuk Alat Jarak
with st.sidebar.expander("🚗 Alat Kira Jarak Pemanduan", expanded=False):
    facility_1 = st.selectbox("Fasiliti Mula", filtered_df['Name'].tolist())
    fac_2_options = filtered_df[filtered_df['Name'] != facility_1]['Name'].tolist()
    facility_2 = st.selectbox("Fasiliti Destinasi", fac_2_options)

    distance_km = None
    route_line = None

    if facility_1 and facility_2:
        coords_1 = (filtered_df[filtered_df['Name'] == facility_1]['Latitude'].values[0], filtered_df[filtered_df['Name'] == facility_1]['Longitude'].values[0])
        coords_2 = (filtered_df[filtered_df['Name'] == facility_2]['Latitude'].values[0], filtered_df[filtered_df['Name'] == facility_2]['Longitude'].values[0])
        
        with st.spinner("Mengira laluan..."):
            distance_km, route_line = get_driving_route(coords_1, coords_2)
                
        if distance_km is not None:
            st.success(f"**Jarak Pemanduan:** {distance_km:.2f} km")
        else:
            st.error("Ralat mendapatkan laluan.")

# 4. PETA (Minimalist)
m = folium.Map(location=[3.75, 102.75], zoom_start=8, min_zoom=7, tiles="CartoDB positron")

for index, row in filtered_df.iterrows():
    popup_html = f"""
    <div style="width: 250px; font-family: Arial, sans-serif;">
        <h4 style="margin-top: 0; margin-bottom: 5px; color: #2C3E50;">{row['Name']}</h4>
        <p style="margin: 2px 0; font-size: 12px; color: gray;"><b>Daerah:</b> {row['District']}</p>
        <hr style="margin: 5px 0;">
        <p style="margin: 2px 0; color: #d35400;"><b>Populasi:</b> {row['Populasi']:,} orang</p>
        <p style="margin: 4px 0;"><b>Pegawai Farmasi:</b> {row['Pegawai_Farmasi']}</p>
        <p style="margin: 4px 0;"><b>Penolong Pegawai:</b> {row['Penolong_Pegawai']}</p>
    </div>
    """
    
    is_main_hub = "Hospital" in str(row['Name']) or "Bahagian" in str(row['Name'])
    icon_color = "red" if is_main_hub else "blue"
    
    folium.Marker(
        [row['Latitude'], row['Longitude']],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=row['Name'],
        icon=folium.Icon(color=icon_color, icon="info-sign")
    ).add_to(m)

if route_line:
    folium.PolyLine(route_line, color="#8E44AD", weight=5, opacity=0.8).add_to(m)

if not filtered_df.empty:
    if route_line:
        m.fit_bounds([[min(p[0] for p in route_line), min(p[1] for p in route_line)], 
                      [max(p[0] for p in route_line), max(p[1] for p in route_line)]])
    else:
        sw = filtered_df[['Latitude', 'Longitude']].min().values.tolist()
        ne = filtered_df[['Latitude', 'Longitude']].max().values.tolist()
        m.fit_bounds([sw, ne])

# Paparkan Peta
st_folium(m, width=1000, height=550)

# 5. JADUAL DATA & BUTANG MUAT TURUN
st.markdown("---")
col_table, col_btn = st.columns([8, 2])

with col_table:
    st.subheader("Data Perincian Anggota Mengikut Fasiliti")

with col_btn:
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Muat Turun CSV",
        data=csv_data,
        file_name='Taburan_Anggota_Farmasi_Pahang.csv',
        mime='text/csv',
    )

clean_table = filtered_df[['Name', 'District', 'Populasi', 'Pegawai_Farmasi', 'Penolong_Pegawai']]
st.dataframe(clean_table, use_container_width=True)
