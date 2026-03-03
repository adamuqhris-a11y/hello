import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

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
    
    # 1. Bina Poligon (Geometri Utama)
    for _, row in df.iterrows():
        coords.append([float(row['E']), float(row['N'])])
    coords.append([float(df.iloc[0]['E']), float(df.iloc[0]['N'])]) # Tutup poligon
    
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

    # 2. Bina Titik (Points) untuk setiap Stesen (Untuk Label STN di QGIS)
    for i, row in df.iterrows():
        p1 = [row['E'], row['N']]
        p2 = [df.iloc[(i + 1) % len(df)]['E'], df.iloc[(i + 1) % len(df)]['N']]
        brg, dist, _ = kira_bearing_jarak(p1, p2)

        point_feature = {
            "type": "Feature",
            "properties": {
                "Layer": "Stesen",
                "STN": int(row['STN']),
                "Easting": row['E'],
                "Northing": row['N'],
                "Bearing_Ke_Next": brg,
                "Jarak_m": round(dist, 3)
            },
            "geometry": {
                "type": "Point",
                "coordinates": [float(row['E']), float(row['N'])]
            }
        }
        features.append(point_feature)
    
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    return json.dumps(geojson_data, indent=4)

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="PUO Geomatik", layout="wide")

# --- Sidebar ---
st.sidebar.header("⚙️ Konfigurasi")
uploaded_logo = st.sidebar.file_uploader("Muat naik Logo Organisasi", type=["png", "jpg", "jpeg"])

# --- Header ---
col_logo, col_text = st.columns([1.5, 4], vertical_alignment="center") 
with col_logo:
    if uploaded_logo is not None:
        st.image(uploaded_logo, width=250) 
    else:
        st.image("https://upload.wikimedia.org/wikipedia/ms/thumb/0/05/Logo_PUO.png/200px-Logo_PUO.png", width=250)
with col_text:
    st.markdown("<h3 style='margin:0;'>POLITEKNIK UNGKU OMAR</h3>", unsafe_allow_html=True)
    st.markdown("<p style='margin:0; font-size: 1.1rem;'>Jabatan Kejuruteraan Geomatik - Sistem Plot Poligon</p>", unsafe_allow_html=True)

st.divider()

# --- Bahagian Muat Naik Fail ---
uploaded_file = st.file_uploader("📂 Muat naik fail CSV (STN, E, N)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.subheader("📍 Jadual Koordinat Stesen")
    st.dataframe(df.set_index('STN'), use_container_width=True)

    if 'E' in df.columns and 'N' in df.columns:
        if 'tampilkan_luas' not in st.session_state:
            st.session_state.tampilkan_luas = False

        luas_semasa = kira_luas(df['E'].values, df['N'].values)

        # --- Sidebar Eksport QGIS ---
        st.sidebar.subheader("🚀 Eksport ke QGIS")
        geojson_output = convert_to_geojson(df, luas_semasa)
        
        # Butang Muat Turun
        st.sidebar.download_button(
            label="🌍 MUAT TURUN FAIL QGIS (.geojson)",
            data=geojson_output,
            file_name="plot_puo_qgis.geojson",
            mime="application/json",
            help="Klik untuk muat turun fail yang boleh dibuka terus dalam QGIS.",
            type="primary"
        )
        st.sidebar.info("💡 Cara buka: Tarik fail yang dimuat turun terus ke dalam skrin QGIS anda.")

        # Plot Matplotlib
        fig, ax = plt.subplots(figsize=(10, 10)) 
        ax.grid(True, linestyle='--', alpha=0.6, color='gray', zorder=0) 
        
        points = df[['E', 'N']].values
        n_points = len(points)
        cx, cy = np.mean(df['E']), np.mean(df['N'])

        for i in range(n_points):
            p1, p2 = points[i], points[(i + 1) % n_points]
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='black', marker='o', 
                    linewidth=3, markersize=8, markerfacecolor='white', zorder=4)
            
            brg_str, dist, brg_val = kira_bearing_jarak(p1, p2)
            mid_x, mid_y = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            mag = np.sqrt(dx**2 + dy**2)
            nx, ny = -dy/mag, dx/mag
            offset_val = 0.4  

            if ((mid_x + nx) - cx)**2 + ((mid_y + ny) - cy)**2 < (mid_x - cx)**2 + (mid_y - cy)**2:
                nx, ny = -nx, -ny
            
            rot = 90 - brg_val
            if rot < -90: rot += 180
            if rot > 90: rot -= 180

            ax.text(mid_x + nx*offset_val, mid_y + ny*offset_val, brg_str, 
                    color='red', fontsize=10, fontweight='bold', ha='center', va='center', rotation=rot, zorder=5)
            ax.text(mid_x - nx*offset_val, mid_y - ny*offset_val, f"{dist:.3f}m", 
                    color='blue', fontsize=9, fontweight='bold', ha='center', va='center', rotation=rot, zorder=5)

        for i, row in df.iterrows():
            vx, vy = row['E'] - cx, row['N'] - cy
            dist_from_center = np.sqrt(vx**2 + vy**2)
            offset_dist = 0.5 
            ax.text(row['E'] + (vx/dist_from_center)*offset_dist, row['N'] + (vy/dist_from_center)*offset_dist, 
                    f"{int(row['STN'])}", fontsize=11, fontweight='bold', ha='center', va='center', zorder=6,
                    bbox=dict(facecolor='yellow', alpha=0.8, edgecolor='black', boxstyle='round,pad=0.15'))

        if st.session_state.tampilkan_luas:
            ax.text(cx, cy, f"LUAS\n{luas_semasa:.3f} m²", fontsize=16, color='darkgreen', fontweight='bold', 
                    ha='center', va='center', zorder=7, bbox=dict(facecolor='white', alpha=0.8, edgecolor='darkgreen', boxstyle='round'))
            ax.fill(df['E'], df['N'], alpha=0.1, color='green', zorder=1)

        ax.set_aspect('equal')
        st.pyplot(fig, use_container_width=True)

        if st.button('📐 Kira & Papar Luas'):
            st.session_state.tampilkan_luas = True
            st.rerun()
            