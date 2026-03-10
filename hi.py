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

LOGO_URL = "https://th.bing.com/th/id/R.7845becf994d6c6a0b2afe8147ecbbf4?rik=l%2bMV7v5yBzHn5g&riu=http%3a%2f%2f1.bp.blogspot.com%2f-wQXM8Oe-ImA%2fTXrQ7Npc7uI%2fAAAAAAAAE34%2f2ref_vtbT5k%2fs1600%2fPoliteknik%252BUngku%252BOmar.png&ehk=IjCxLkjx3O7Lb2LSgWsvprPJ5Dvm%2fAHQVB35yucEm6Q%3d&risl=&pid=ImgRaw&r=0"

# 2. SISTEM LOGIN (DIKEMASKINI: 3 USER SAHAJA)
def load_users():
    # Menetapkan 3 ID pengguna seperti yang diminta
    senarai_id = ["adam", "aina", "abu"]
    
    # Kata laluan yang sama untuk semua user
    PASSWORD_SERAGAM = "123456" 
    
    return {user: PASSWORD_SERAGAM for user in senarai_id}

if "user_db" not in st.session_state: 
    st.session_state["user_db"] = load_users()
if "logged_in" not in st.session_state: 
    st.session_state["logged_in"] = False
if "current_user" not in st.session_state: 
    st.session_state["current_user"] = ""

def auth_interface():
    _, col2, _ = st.columns([1, 1.8, 1])
    with col2:
        st.markdown(f"<div style='text-align: center;'><br><img src='{LOGO_URL}' width='80'><h2>Sistem Geomatik PUO</h2></div>", unsafe_allow_html=True)
        with st.form("login_form"):
            u_id = st.text_input("ID Pengguna")
            u_pw = st.text_input("Kata Laluan", type="password")
            if st.form_submit_button("Masuk", use_container_width=True):
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
    try: return Transformer.from_crs(f"epsg:{epsg}", "epsg:4326", always_xy=True)
    except: return None

def kira_data_garisan(p1, p2):
    de, dn = p2['E'] - p1['E'], p2['N'] - p1['N']
    dist = math.sqrt(de**2 + dn**2)
    angle = math.degrees(math.atan2(de, dn))
    if angle < 0: angle += 360
    brg_str = f"{int(angle)}°{int((angle%1)*60):02d}'{int(((angle%1)*60%1)*60):02d}\""
    rot_angle = angle - 90
    if 90 < angle < 270: rot_angle += 180
    return brg_str, round(dist, 3), rot_angle

# 3. SIDEBAR
st.sidebar.markdown(f"**Sesi:** `{st.session_state['current_user']}`")
if st.sidebar.button("🚪 Log Keluar"):
    st.session_state["logged_in"] = False
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("🎯 Penentukuran (Offset)")
off_n = st.sidebar.slider("Utara/Selatan (m)", -30.0, 30.0, 0.0)
off_e = st.sidebar.slider("Timur/Barat (m)", -30.0, 30.0, 0.0)
epsg_input = st.sidebar.text_input("Kod EPSG", value="4390")

# 4. MAIN LOGIC
uploaded_file = st.sidebar.file_uploader("Muat naik CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    tf = get_transformer(epsg_input)
    
    if tf:
        df_mod = df.copy()
        df_mod['E_adj'], df_mod['N_adj'] = df_mod['E'] + off_e, df_mod['N'] + off_n
        lons, lats = tf.transform(df_mod['E_adj'].values, df_mod['N_adj'].values)
        df['lat'], df['lon'] = lats, lons
        
        # PETA
        m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=21, max_zoom=24)
        folium.TileLayer("https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attr="Google", max_zoom=24).add_to(m)
        
        # Info Lot Popup
        area_m2 = Polygon(zip(df['E'], df['N'])).area
        lot_html = f"<b>Info Lot</b><br>Luas: {area_m2:.3f} m²<br>Surveyor: {st.session_state['current_user']}"
        folium.Polygon(df[['lat', 'lon']].values.tolist(), color="yellow", fill=True, fill_opacity=0.2, weight=3, popup=folium.Popup(lot_html, max_width=200)).add_to(m)

        points_for_geojson = []
        for i in range(len(df)):
            p1, p2 = df.iloc[i], df.iloc[(i+1)%len(df)]
            brg, dist, rot = kira_data_garisan(p1, p2)
            
            # POPUP SETIAP STESEN
            stn_popup_html = f"""
            <div style="font-family: Arial; width: 160px
