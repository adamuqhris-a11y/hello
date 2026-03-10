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

# Logo asal (Fallback jika fail tempatan tiada)
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
        # Menampilkan Logo PUO yang anda muat naik
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
        
        with st.expander("Tukar Kata Laluan Baru"):
            with st.form("change_pw_form"):
                new_pw = st.text_input("Masukkan Kata Laluan Baru", type="password")
                confirm_pw = st.text_input("Sahkan Kata Laluan Baru", type="password")
                change_btn = st.form_submit_button("Kemaskini Kata Laluan")
                if change_btn:
                    if new_pw == confirm_pw and new_pw != "":
                        save_password(new_pw)
                        st.session_state["user_db"] = load_users()
                        st.success("Kata laluan telah disimpan secara kekal!")
                    else:
                        st.error("Kata laluan tidak sepadan!")

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
    # PEMBETULAN SINTAKS DI SINI
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
st.sidebar.subheader("⚙️ Tetapan Paparan Peta")
show_sat = st.sidebar.checkbox("Paparkan Imej Satelit", value=True)
show_stn = st.sidebar.checkbox("Paparkan Label Stesen", value=True)
show_data = st.sidebar.checkbox("Paparkan Bering & Jarak", value=True)
show_poly = st.sidebar.checkbox("Paparkan Poligon Lot", value=True)

st.sidebar.divider()
st.sidebar.subheader("🎯 Penentukuran (Offset)")
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
        
        m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=20, max_zoom=24, control_scale=True)
        
        if show_sat:
            folium.TileLayer(
                tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", 
                attr="Google Satellite", max_zoom=24, name="Satelit"
            ).add_to(m)
        else:
            folium.TileLayer(name="Standard").add_to(m)

        area_m2 = Polygon(zip(df['E'], df['N'])).area
        lot_html = f"<b>Info Lot</b><br>Luas: {area_m2:.3f} m²<br>Surveyor: {st.session_state['current_user']}"
        
        if show_poly:
            folium.Polygon(
                df[['lat', 'lon']].values.tolist(), 
                color="yellow", fill=True, fill_opacity=0.2, weight=3, 
                popup=folium.Popup(lot_html, max_width=200)
            ).add_to(m)

        points_for_geojson = []
        for i in range(len(df)):
            p1, p2 = df.iloc[i], df.iloc[(i+1)%len(df)]
            brg, dist, rot = kira_data
