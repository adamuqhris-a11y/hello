import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import folium
from streamlit_folium import st_folium

# 1. Fungsi DMS (Darjah, Minit, Saat)
def to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = round((((deg - d) * 60) - m) * 60, 0)
    if s == 60: m += 1; s = 0
    if m == 60: d += 1; m = 0
    return f"{d}°{m:02d}'{s:02.0f}\""

# 2. Fungsi Kira Bearing dan Jarak
def kira_bearing_jarak(p1, p2):
    de = p2[0] - p1[0]
    dn = p2[1] - p1[1]
    jarak = np.sqrt(de**2 + dn**2)
    angle = np.degrees(np.arctan2(de, dn))
    bearing = angle if angle >= 0 else angle + 360
    return to_dms(bearing), jarak, bearing

# 3. Fungsi Kira Luas (Metode Shoelace)
def kira_luas(x, y):
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

# --- FUNGSI EKSPORT KE QGIS (GEOJSON) ---
def convert_to_geojson(df, luas):
    features = []
    coords = []
    
    for _, row in df.iterrows():
        coords.append([float(row['E']), float(row['N'])])
    coords.append([float(df.iloc[0]['E']), float(df.iloc[0]['N'])]) 
    
    poly_feature = {
        "type": "Feature",
        "properties": {
            "Layer": "Lot_Poligon",
            "Luas_m2": round(luas, 3),
            "Program": "PUO Geomatik Plotter"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [coords]
        }
    }
    features.append(poly_feature)

    for i, row in df.iterrows():
        point_feature = {
            "type": "Feature",
            "properties": {
                "Layer": "Stesen",
                "STN": int(row['STN']),
                "Easting": row['E'],
                "Northing": row['N']
            },
            "geometry": {
                "type": "Point",
                "coordinates": [float(row['E']), float(row['N'])]
            }
        }
        features.append(point_feature)
    
    geojson_data = {"type": "FeatureCollection", "features": features}
    return json.dumps(geojson_data, indent=4)

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="PUO Geomatik Plotter", layout="wide")

# --- Header ---
col_logo, col_text = st.columns([1.5, 4], vertical_alignment="center") 
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/ms/thumb/0/05/Logo_PUO.png/200px-Logo_PUO.png", width=200)
with col_text:
    st.markdown("<h2 style='margin:0;'>POLITEKNIK UNGKU OMAR</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='margin:0;'>Jabatan Kejuruteraan Geomatik - Sistem Plotter & Google Satellite</h4>", unsafe_allow_html=True)

st.divider()

# --- Sidebar ---
st.sidebar.header("📂 Data Input")
uploaded_file = st.sidebar.file_uploader("Muat naik fail CSV (STN, E, N)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    luas_semasa = kira_luas(df['E'].values, df['N'].values)

    # --- TAB NAVIGATION ---
    tab1, tab2, tab3 = st.tabs(["🗺️ Peta Satelit (Google)", "📐 Pelan Teknikal", "📊 Data Jadual"])

    with tab3:
        st.subheader("📍 Jadual Koordinat Stesen")
        st.dataframe(df.set_index('STN'), use_container_width=True)
        
        # Download Button
        geojson_output = convert_to_geojson(df, luas_semasa)
        st.download_button(
            label="🌍 Eksport ke QGIS (.geojson)",
            data=geojson_output,
            file_name="plot_puo_qgis.geojson",
            mime="application/json"
        )

    with tab1:
        st.subheader("Peta Satelit Interaktif")
        # Titik Tengah
        center_n = df['N'].mean()
        center_e = df['E'].mean()

        # Bina Folium Map
        m = folium.Map(location=[center_n, center_e], zoom_start=18, control_scale=True)

        # Tambah Google Satellite Layer
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Satellite',
            overlay=False,
            control=True
        ).add_to(m)

        # Bina Poligon untuk Folium
        folium_coords = [[row['N'], row['E']] for _, row in df.iterrows()]
        
        folium.Polygon(
            locations=folium_coords,
            color="cyan",
            weight=3,
            fill=True,
            fill_opacity=0.2,
            tooltip=f"Luas: {luas_semasa:.3f} m²"
        ).add_to(m)

        # Tambah Marker
        for _, row in df.iterrows():
            folium.CircleMarker(
                location=[row['N'], row['E']],
                radius=4,
                color="yellow",
                fill=True,
                popup=f"STN: {int(row['STN'])}"
            ).add_to(m)

        # Papar Peta
        st_folium(m, width="100%", height=600)

    with tab2:
        st.subheader("Pelan Plotting Geomatik")
        
        # Plot Matplotlib
        fig, ax = plt.subplots(figsize=(10, 10)) 
        ax.grid(True, linestyle='--', alpha=0.3) 
        
        points = df[['E', 'N']].values
        n_points = len(points)
        cx, cy = np.mean(df['E']), np.mean(df['N'])

        for i in range(n_points):
            p1, p2 = points[i], points[(i + 1) % n_points]
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='black', marker='o', 
                    linewidth=2, markersize=6, markerfacecolor='white', zorder=4)
            
            brg_str, dist, brg_val = kira_bearing_jarak(p1, p2)
            mid_x, mid_y = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            
            # Labeling logic
            rot = 90 - brg_val
            if rot < -90: rot += 180
            if rot > 90: rot -= 180

            ax.text(mid_x, mid_y, f"{brg_str}\n{dist:.3f}m", 
                    color='blue', fontsize=8, ha='center', va='center', rotation=rot)

        # Label Nombor Stesen
        for i, row in df.iterrows():
            ax.text(row['E'], row['N'], f" {int(row['STN'])}", fontsize=10, fontweight='bold')

        ax.set_aspect('equal')
        ax.set_xlabel("Easting (E)")
        ax.set_ylabel("Northing (N)")
        st.pyplot(fig)

        st.success(f"Luas Keseluruhan: **{luas_semasa:.3f} meter persegi**")

else:
    st.info("Sila muat naik fail CSV untuk memulakan pemetaan.")
