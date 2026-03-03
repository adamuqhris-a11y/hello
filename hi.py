import streamlit as st
import pandas as pd
# ... (semua import lain) ...

# --- 1. Letak fungsi-fungsi kat atas sekali ---
def to_dms(deg):
    # isi fungsi...
    return 

# --- 2. Bahagian Upload (Mesti sebelum Line 10 tadi!) ---
uploaded_file = st.file_uploader("📂 Muat naik fail CSV", type=["csv"])

# --- 3. Baru boleh guna 'if uploaded_file' ---
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    # ... sambung kod kau kat sini ...
