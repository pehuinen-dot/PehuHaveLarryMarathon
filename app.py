import streamlit as st
import gpxpy
import pandas as pd
import plotly.express as px
import os
import glob
import datetime

st.set_page_config(
    page_title="PehuHaveLarry Sports & Marathon Dashboard", 
    layout="wide",
    page_icon="🏆"
)

st.title("🏆 PehuHaveLarry Multi-Sport Dashboard")
st.write("Vuoden 2026 kaikkien lajien harjoitukset, kalorikulutus ja maksimitulokset!")

# Lajien ikonit ja symbolit
SPORT_ICONS = {
    'Jääkiekko': '🏒',
    'Juoksu': '🏃',
    'Kävely': '🚶',
    'Pyöräily': '🚴',
    'Hiihto': '🎿',
    'Padel': '🎾',
    'Golf': '⛳',
    'Kuntosali / Voimailu': '🏋️',
    'Uinti': '🏊',
    'Muu laji': '🎯'
}

juoksijan_nimi = st.sidebar.text_input("Urheilijan nimi", "Antti")

@st.cache_data
def load_all_gpx(folder_path="data"):
    records = []
    gpx_files = glob.glob(os.path.join(folder_path, "*.gpx")) + glob.glob(os.path.join(folder_path, "*.GPX"))
    
    for filepath in gpx_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                gpx = gpxpy.parse(f)
                
            data = []
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        hr = None
                        for ext in point.extensions:
                            for child in ext:
                                if child.tag.endswith('hr'):
                                    hr = int(child.text)
                        
                        data.append({
                            'time': point.time,
                            'elevation': point.elevation,
                            'hr': hr
                        })
            
            df_points = pd.DataFrame(data)
            if df_points.empty:
                continue
                
            fname = os.path.basename(filepath).lower()
            track_name = gpx.tracks[0].name.lower() if gpx.tracks and gpx.tracks[0].name else ""
            full_text = fname + " " + track_name
            
            # Tunnistetaan laji tiedostonimen tai treenin nimen perusteella
            if 'hockey' in full_text or 'jaakiekko' in full_text or 'ice' in full_text:
                laji = 'Jääkiekko'
            elif 'cycling' in full_text or 'bike' in full_text or 'pyoraily' in full_text:
                laji = 'Pyöräily'
            elif 'golf' in full_text:
                laji = 'Golf'
            elif 'ski' in full_text or 'hiihto' in full_text:
                laji = 'Hiihto'
            elif 'padel' in full_text or 'tennis' in full_text or 'racket' in full_text:
                laji = 'Padel'
            elif 'gym' in full_text or 'sali' in full_text or 'weight' in full_text:
                laji = 'Kuntosali / Voimailu'
            elif 'swim' in full_text or 'uinti' in full_text:
                laji = 'Uinti'
            elif 'walking' in full_text or 'walk' in full_text or 'kavely' in full_text:
                laji = 'Kävely'
            elif 'running' in full_text or 'run' in full_text or 'juoksu' in full_text:
                laji = 'Juoksu'
            else:
                laji = 'Muu laji'

            dist_km = gpx.length_2d() / 1000.0
            start_time = df_points['time'].min()
            end_time = df_points['time'].max()
            duration_min = (end_time - start_time).total_seconds() / 60.0 if start_time and end_time else 0
            
            speed_kmh = (dist_km / (duration_min / 60.0)) if duration_min > 0 else 0
            avg_hr = df_points['hr'].mean() if 'hr' in df_points and df_points['hr'].notnull().any() else None
            max_hr = df_points['hr'].max() if 'hr' in df_points and df_points['hr'].notnull().any() else None

            # Kalorien laskenta sykedatan tai lajityypin perusteella
            calories = None
            if avg_hr and duration_min > 0:
                # Syke-pohjainen kalorikaava (mies ~88kg)
                cal_per_min = (-55.0969 + (36 * 0.2017) - (88 * 0.09036) + (avg_hr * 0.6309)) / 4.184
                if cal_per_min > 0:
                    calories = round(cal_per_min * duration_min, 0)
            elif duration_min > 0:
                # MET-arviokaava jos syke puuttuu
                met_values = {'Juoksu': 10, 'Jääkiekko': 9, 'Pyöräily': 8, 'Kävely': 4, 'Hiihto': 9, 'Padel': 7}
                met = met_values.get(laji, 6)
                calories = round((met * 3.5 * 88 / 200) * duration_min, 0)

            records.append({
                'Urheilija': juoksijan_nimi,
                'Päivämäärä': start_time.date() if start_time else None,
                'Vuosi': start_time.year if start_time else None,
                'Laji': laji,
                'Matka (km)': round(dist_km, 2),
                'Kesto (min)': round(duration_min, 1),
                'Keskinopeus (km/h)': round(speed_kmh, 1),
                'Keskisyke': round(avg_hr, 0) if avg_hr else None,
                'Maksimisyke': round(max_hr, 0) if max_hr else None,
                'Kalorit (kcal)': calories
            })
        except Exception as e:
            continue
            
    return pd.DataFrame(records)

df = load_all_gpx("data")

if not df.empty:
    df['Päivämäärä'] = pd.to_datetime(df['Päivämäärä'])
    
    # Näytetään vuoden 2026 data (tai kaikki jos muuta löytyy)
    df_2026 = df[df['Vuosi'] == 2026].copy()
    if df_2026.empty:
        df_2026 = df.copy()
        
    st.subheader("📊 Vuoden 2026 Yhteenveto & Maksimit")
    
    # Yleismittarit
    col_tot1, col_tot2, col_tot3, col_tot4 = st.columns(4)
    col_tot1.metric("Kaikki treenit 2026", f"{len(df_2026)} kpl")
    col_tot2.metric("Aikaa urheiltu", f"{round(df_2026['Kesto (min)'].sum() / 60, 1)} h")
    col_tot3.metric("Kokonaiskilometrit", f"{round(df_2026['Matka (km)'].sum(), 1)} km")
    
    tot_cal = int(df_2026['Kalorit (kcal)'].sum()) if df_2026['Kalorit (kcal)'].notnull().any() else 0
    col_tot4.metric("Kokonaiskalorit", f"{tot_cal:,} kcal".replace(",", " "))
    
    st.write("---")
    st.subheader("🔥 Lajikohtaiset kortit ja maksimitulokset 2026")
    
    unique_sports = df_2026['Laji'].unique()
    
    if len(unique_sports) > 0:
        for sport in sorted(unique_sports):
            sport_df = df_2026[df_2026['Laji'] == sport]
            icon = SPORT_ICONS.get(sport, '🎯')
            
            with st.expander(f"{icon} **{sport}** — {len(sport_df)} harjoitusta vuonna 2026", expanded=True):
                c1, c2, c3, c4, c5 = st.columns(5)
                
                c1.metric("Harjoituksia", f"{len(sport_df)} kpl")
                c2.metric("Aikaa yhteensä", f"{round(sport_df['Kesto (min)'].sum() / 60, 1)} h")
                c3.metric("Max kesto / treeni", f"{round(sport_df['Kesto (min)'].max(), 0)} min")
                
                max_kcal = int(sport_df['Kalorit (kcal)'].max()) if sport_df['Kalorit (kcal)'].notnull().any() else 0
                c4.metric("Max kalorit / treeni", f"{max_kcal} kcal")
                
                max_hr_val = int(sport_df['Maksimisyke'].max()) if sport_df['Maksimisyke'].notnull().any() else "-"
                c5.metric("Maksimisyke (HR)", f"{max_hr_val} bpm")
                
                if sport_df['Matka (km)'].sum() > 0:
                    st.caption(f"📍 Yhteensä matkaa: **{round(sport_df['Matka (km)'].sum(), 1)} km** | Pisin kerta: **{round(sport_df['Matka (km)'].max(), 1)} km**")

    st.write("---")
    st.subheader("📈 Kalorikulutus kuukausittain 2026")
    
    df_2026['Kuukausi'] = df_2026['Päivämäärä'].dt.strftime('%Y-%m')
    df_monthly = df_2026.groupby(['Kuukausi', 'Laji'])['Kalorit (kcal)'].sum().reset_index()
    
    fig_cal = px.bar(
        df_monthly, 
        x="Kuukausi", 
        y="Kalorit (kcal)", 
        color="Laji",
        title="Poltetut kalorit lajeittain kuukausittain",
        barmode="stack"
    )
    fig_cal.update_layout(template="plotly_white")
    st.plotly_chart(fig_cal, use_container_width=True)

    st.subheader("📋 Vuoden 2026 kaikki treenit listattuna")
    st.dataframe(df_2026.sort_values("Päivämäärä", ascending=False), use_container_width=True)

else:
    st.info("Kansiossa 'data/' ei ole vielä GPX-tiedostoja tai lataus on kesken.")
