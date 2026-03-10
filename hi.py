import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import math
from pyproj import Transformer
import geopandas as gpd
from shapely.geometry import Polygon, Point
import json
import os

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="PUO Geomatics Pro", layout="wide")

LOGO_URL_KECIL = "https://th.bing.com/th/id/R.7845becf994d6c6a0b2afe8147ecbbf4?rik=l%2bMV7v5yBzHn5g&riu=http%3a%2f%2f1.bp.blogspot.com%2f-wQXM8Oe-ImA%2fTXrQ7Npc7uI%2fAAAAAAAAE34%2f2ref_vtbT5k%2fs1600%2fPoliteknik%252BUngku%252BOmar.png&ehk=IjCxLkjx3O7Lb2LSgWsvprPJ5Dvm%2fAHQVB35yucEm6Q%3d&risl=&pid=ImgRaw&r=0"

# 2. SISTEM LOGIN
def get_stored_password():
    file_path = "password.txt"
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("123456")
        return "123456"
    with open(file_path, "r") as f:
        return f.read().strip()

def save_password(new_pw):
    with open("password.txt", "w") as f:
        f.write(new_pw)

def load_users():
    current_pw = get_stored_password()
    senarai_id = ["adam", "aina", "abu"]
    return {user: current_pw for user in senarai_id}

if "user_db" not in st.session_state: 
    st.session_state["user_db"] = load_users()
if "logged_in" not in st.session_state: 
    st.session_state["logged_in"] = False
if "current_user" not in st.session_state: 
    st.session_state["current_user"] = ""

def auth_interface():
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("politeknik-ungku-umar-seeklogo-removebg-preview.png.png", use_container_width=True)
        except:
            st.markdown(f"<center><img src='{LOGO_URL_KECIL}' width='100'></center>", unsafe_allow_html=True)
            
        st.markdown("<h2 style='text-align: center;'>SISTEM GEOMATIK PUO</h2>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            u_id = st.text_input("ID Pengguna")
            u_pw = st.text_input("Kata Laluan", type="password")
            submit = st.form_submit_button("Masuk", use_container_width=True)
            if submit:
                st.session_state["user_db"] = load_users()
                if u_id in st.session_state["user_db"] and st.session_state["user_db"][u_id] == u_pw:
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = u_id
                    st.rerun()
                else: 
                    st.error("ID atau Kata Laluan salah!")

if not st.session_state["logged_in"]: 
    auth_interface()
    st.stop()

# --- FUNGSI GEOMETRI ---
@st.cache_resource
def get_transformer(epsg):
    try: 
        return Transformer.from_crs(f"epsg:{epsg}", "epsg:4326", always_xy=True)
    except: 
        return None

def kira_data_garisan(p1, p2):
    de, dn = p2['E'] - p1['E'], p2['N'] - p1['N']
    dist = math.sqrt(de**2 + dn**2)
    angle = math.degrees(math.atan2(de, dn))
    if angle < 0: angle += 360
    
    # PEMBETULAN BARIS 84 (Formula DMS yang lengkap)
    d = int(angle)
    m = int((angle % 1) * 60)
    s = int(((angle % 1) * 60 % 1) * 60)
    brg_str = f"{d}°{m:02d}'{s:02d}\""
    
    rot_angle = angle - 90
    if 90 < angle < 270: rot_angle += 180
    return brg_str, round(dist, 3), rot_angle

# 3. SIDEBAR
st.sidebar.markdown(f"**Sesi:** `{st.session_state['current_user']}`")
if st.sidebar.button("Log Keluar"):
    st.session_state["logged_in"] = False
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("Tetapan Paparan Peta")
show_sat = st.sidebar.checkbox("Paparkan Imej Satelit", value=True)
show_stn = st.sidebar.checkbox("Paparkan Label Stesen", value=True)
show_data = st.sidebar.checkbox("Paparkan Bering & Jarak", value=True)
show_poly = st.sidebar.checkbox("Paparkan Poligon Lot", value=True)

st.sidebar.divider()
st.sidebar.subheader("Penentukuran (Offset)")
off_n = st.sidebar.slider("Utara/Selatan (m)", -30.0, 30.0, 0.0)
off_e = st.sidebar.slider("Timur/Barat (m)", -30.0, 30.0, 0.0)
epsg_input = st.sidebar.text_input("Kod EPSG", value="4390")

# 4. MAIN LOGIC
st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <img src='{LOGO_URL_KECIL}' width='50' style='margin-right:15px;'>
        <h1 style='margin:0;'>SISTEM GEOMATIK PUO PRO</h1>
    </div>
    <hr style='margin-top:0;'>
""", unsafe_allow_html=True)

uploaded_file = st.sidebar.file_uploader("Muat naik CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    tf = get_transformer(epsg_input)
    
    if tf:
        df_mod = df.copy()
        df_mod['E_adj'], df_mod['N_adj'] = df_mod['E'] + off_e, df_mod['N'] + off_n
        lons, lats = tf.transform(df_mod['E_adj'].values, df_mod['N_adj'].values)
        df['lat'], df['lon'] = lats, lons
        
        m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=20, max_zoom=24)
        
        if show_sat:
            folium.TileLayer(
                tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", 
                attr="Google Satellite", max_zoom=24, name="Satelit"
            ).add_to(m)
        else:
            folium.TileLayer(name="Standard").add_to(m)

        area_m2 = Polygon(zip(df['E'], df['N'])).area
        
        if show_poly:
            folium.Polygon(
                df[['lat', 'lon']].values.tolist(), 
                color="yellow", fill=True, fill_opacity=0.2, weight=3
            ).add_to(m)

        for i in range(len(df)):
            p1 = df.iloc[i]
            p2 = df.iloc[(i+1) % len(df)]
            brg, dist, rot = kira_data_garisan(p1, p2)
            
            if show_stn:
                folium.CircleMarker(
                    location=[p1['lat'], p1['lon']], radius=5, color="white", weight=2, 
                    fill=True, fill_color="red", fill_opacity=1,
                    tooltip=f"STN {int(p1['STN'])}"
                ).add_to(m)
            
            if show_data:
                mid_lat, mid_lon = (p1['lat']+p2['lat'])/2, (p1['lon']+p2['lon'])/2
                html_label = f'<div style="transform: rotate({rot}deg); font-size: 8pt; color: #00FF00; font-weight: bold; text-shadow: 1px 1px 2px black; text-align: center; width: 100px; margin-left: -50px;">{brg}<br>{dist}m</div>'
                folium.Marker([mid_lat, mid_lon], icon=folium.DivIcon(html=html_label)).add_to(m)

        st_folium(m, width="100%", height=600, returned_objects=[])
        st.metric("Luas (m²)", f"{area_m2:.3f}")
    else: 
        st.error("Ralat EPSG!")
else: 
    st.info("Sila muat naik fail CSV untuk memulakan.")
