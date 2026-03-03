import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

# --- TAMBAHAN: Fungsi Papar Peta Satelit ---
def papar_peta_satelit(df):
    # NOTA: Kod ini mengandaikan E/N kau adalah dalam Lat/Lon. 
    # Jika E/N dalam meter (RSO/UTM), kau perlukan library 'pyproj' untuk convert.
    
    # Ambil titik tengah untuk fokus peta
    avg_lat = df['N'].mean()
    avg_lon = df['E'].mean()
    
    # Bina peta guna Folium
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=18, tiles=None)
    
    # Tambah Layer Google Satellite
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)

    # Tambah Poligon Lot
    locations = df[['N', 'E']].values.tolist()
    locations.append(locations[0]) # Tutup poligon
    
    folium.Polygon(
        locations=locations,
        color='yellow',
        weight=3,
        fill=True,
        fill_color='yellow',
        fill_opacity=0.2
    ).add_to(m)

    # Tambah Marker Stesen
    for i, row in df.iterrows():
        folium.CircleMarker(
            location=[row['N'], row['E']],
            radius=5,
            color='red',
            fill=True,
            popup=f"STN: {int(row['STN'])}"
        ).add_to(m)

    return m

# --- Masukkan dalam bahagian paparan (selepas Matplotlib tadi) ---
st.divider()
st.subheader("🌍 Paparan Google Satellite")
st.info("Pastikan koordinat dalam fail CSV adalah format Latitude/Longitude (WGS84) untuk paparan yang tepat.")

peta = papar_peta_satelit(df)
folium_static(peta)
