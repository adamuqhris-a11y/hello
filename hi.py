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

# URL Logo (Gunakan URL baru atau path fail yang anda muat naik)
LOGO_URL = "https://i.ibb.co/LzXpYyM/politeknik-ungku-omar-seeklogo-removebg-preview-png" 

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
    _, col2, _ = st.columns([1, 1.8, 1])
    with col2:
        st.markdown(f"<div style='text-align: center;'><br><img src='{LOGO_URL}' width='250'><h2>Sistem Geomatik PUO</h2></div>", unsafe_allow_html=True)
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
                        st.success(f

