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

# Link logo asal (Backup)
LOGO_URL_KECIL = "https://th.bing.com/th/id/R.7845becf994d6c6a0b2afe8147ecbbf4?rik=l%2bMV7v5yBzHn5g&riu=http%3a%2f%2f1.bp.blogspot.com%2f-wQXM8Oe-ImA%2fTXrQ7Npc7uI%2fAAAAAAAAE34%2f2ref_vtbT5k%2fs1600%2fPoliteknik%252BUngku%252BOmar.png&ehk=IjCxLkjx3O7Lb2LSgWsvprPJ5Dvm%2fAHQVB35yucEm6Q%3d&risl=&pid=ImgRaw&r=0"

# 2. SISTEM LOGIN (KEKAL KATA LALUAN DALAM FAIL)
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
        # Memaparkan Logo yang anda hantar
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
                        st.success(f"Kata laluan telah disimpan secara kekal!")
                        st.info("Sila log masuk menggunakan kata laluan baru anda.")
                    else:
                        st.error("Kata laluan tidak sepadan atau kosong!")

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
    angle =
