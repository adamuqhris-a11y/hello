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
    st.session_state["user_db"] = load_
