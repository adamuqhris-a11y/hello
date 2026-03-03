# --- 1. LETAK FUNGSI NI KAT ATAS ---
def papar_peta_satelit(df):
    avg_lat = df['N'].mean()
    avg_lon = df['E'].mean()
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=18)
    # ... (kod rest of function) ...
    return m

# --- 2. BARU PANGGIL KAT BAWAH (Line 57 kau tadi) ---
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    # ... kod lain ...
    peta = papar_peta_satelit(df) # Pastikan 'df' ni dah ada isi
    folium_static(peta)
