import streamlit as st
import gpxpy
import pandas as pd
import datetime

st.set_page_config(page_title="PehuHaveLarry Marathon Dashboard", layout="wide")

st.title("🏃‍♂️ PehuHaveLarry Marathon Dashboard")
st.write("Valmistautuminen kohti maratonia!")

# Sivupalkki tiedostojen lataukselle
st.sidebar.header("Treenitiedostot")
uploaded_files = st.sidebar.file_uploader(
    "Lataa GPX-tiedostoja", type=["gpx"], accept_multiple_files=True
)

juoksijan_nimi = st.sidebar.text_input("Juoksijan nimi", "Antti")

# Lajisuodatin sivupalkissa
laji_valinta = st.sidebar.multiselect(
    "Valitse näytettävät lajit",
    ["Juoksu", "Kävely"],
    default=["Juoksu", "Kävely"]
)

@st.cache_data
def parse_gpx(file):
    try:
        gpx = gpxpy.parse(file)
        data = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    # Etsitään syketieto (extension-kentistä), jos sellainen löytyy
                    hr = None
                    for ext in point.extensions:
                        for child in ext:
                            if child.tag.endswith('hr'):
                                hr = int(child.text)
                    
                    data.append({
                        'time': point.time,
                        'latitude': point.latitude,
                        'longitude': point.longitude,
                        'elevation': point.elevation,
                        'hr': hr
                    })
        
        df_points = pd.DataFrame(data)
        if df_points.empty:
            return None
            
        # Tiedostonimi ja oletustyyppi
        fname = file.name.lower()
        
        # Määritetään laji tiedostonimen perusteella
        if 'cycling' in fname or 'bike' in fname:
            laji = 'Pyöräily'
        elif 'golf' in fname:
            laji = 'Golf'
        elif 'walking' in fname or 'walk' in fname:
            laji = 'Kävely'
        elif 'running' in fname or 'run' in fname:
            laji = 'Juoksu'
        else:
            laji = 'Muu'

        # Lasketaan matka ja kesto
        dist_km = gpx.length_2d() / 1000.0
        start_time = df_points['time'].min()
        end_time = df_points['time'].max()
        duration_min = (end_time - start_time).total_seconds() / 60.0 if start_time and end_time else 0
        
        speed_kmh = (dist_km / (duration_min / 60.0)) if duration_min > 0 else 0
        avg_hr = df_points['hr'].mean() if 'hr' in df_points and df_points['hr'].notnull().any() else None

        # Varatietona: jos laji oli 'Muu', tarkistetaan keskinopeudella
        if laji == 'Muu':
            if speed_kmh > 18.0:
                laji = 'Pyöräily'
            elif speed_kmh > 6.0:
                laji = 'Juoksu'
            else:
                laji = 'Kävely'

        return {
            'Juoksija': juoksijan_nimi,
            'Päivämäärä': start_time.strftime('%Y-%m-%d') if start_time else '',
            'Laji': laji,
            'Matka (km)': round(dist_km, 2),
            'Kesto (min)': round(duration_min, 1),
            'Keskinopeus (km/h)': round(speed_kmh, 1),
            'Keskisyke': round(avg_hr, 0) if avg_hr else None
        }
    except Exception as e:
        return None

if uploaded_files:
    records = []
    for f in uploaded_files:
        res = parse_gpx(f)
        if res:
            records.append(res)
            
    if records:
        df = pd.DataFrame(records)
        
        # Suodatetaan valittujen lajien mukaan (Juoksu / Kävely)
        df_filtered = df[df['Laji'].isin(laji_valinta)]
        
        # Avainluvut
        col1, col2, col3 = st.columns(3)
        yhteismatka = df_filtered['Matka (km)'].sum()
        treenien_maara = len(df_filtered)
        pisin_lenkki = df_filtered['Matka (km)'].max() if treenien_maara > 0 else 0
        
        col1.metric("Yhteensä matkaa", f"{yhteismatka:.1f} km")
        col2.metric("Treenien määrä", f"{treenien_maara} kpl")
        col3.metric("Pisin lenkki", f"{pisin_lenkki:.1f} km")
        
        st.subheader("📊 Treenilistaus")
        st.dataframe(df_filtered, use_container_width=True)
        
        # Kehitys kuvaajana
        st.subheader("📈 Kilometrien kehitys")
        if not df_filtered.empty:
            df_chart = df_filtered.sort_values("Päivämäärä")
            st.bar_chart(df_chart, x="Päivämäärä", y="Matka (km)")
else:
    st.info("Lataa GPX-tiedostot vasemmasta sivupalkista aloittaaksesi.")
