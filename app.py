import streamlit as st
import gpxpy
import pandas as pd
import plotly.express as px
import os
import glob

st.set_page_config(
    page_title="PehuHaveLarry Multi-Sport Dashboard", 
    layout="wide",
    page_icon="🏆"
)

st.title("🏆 PehuHaveLarry Multi-Sport Dashboard")
st.write("Kaikki harjoitukset, lajikohtaiset kortit, VO2 Max ja Helsinki–Budapest -haaste!")

SPORT_ICONS = {
    'Golf': '⛳',
    'Luistelu': '⛸️',
    'Kävely': '🚶',
    'Kuntosali': '🏋️',
    'Jääkiekko': '🏒',
    'Maastohiihto': '🎿',
    'Padel': '🎾',
    'Juoksu': '🏃',
    'Pyöräily': '🚴',
    'Lumilautailu': '🏂',
    'Kuntopiiriharjoittelu': '🤸',
    'Kuntopyörä': '🚴‍♂️',
    'Juoksumatto': '🏃‍♂️',
    'Soutu': '🚣',
    'Crosstraining': '💪',
    'Muu laji': '🎯'
}

juoksijan_nimi = st.sidebar.text_input("Urheilijan nimi", "Antti")

@st.cache_data
def load_all_gpx(folder_path="data"):
    records = []
    
    gpx_files = []
    for ext in ('*.gpx', '*.GPX', '*.xml', '*.XML'):
        gpx_files.extend(glob.glob(os.path.join(folder_path, "**", ext), recursive=True))
    
    gpx_files = list(set(gpx_files))

    for filepath in gpx_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                gpx = gpxpy.parse(f)
                
            fname = os.path.basename(filepath).lower()
            track_name = gpx.tracks[0].name.lower() if gpx.tracks and gpx.tracks[0].name else ""
            gpx_type = str(gpx.tracks[0].type).lower() if (gpx.tracks and hasattr(gpx.tracks[0], 'type') and gpx.tracks[0].type) else ""
            full_text = f"{fname} {track_name} {gpx_type}"

            # Tarkennettu lajitunnistus pyydetyn listan mukaan
            if any(w in full_text for w in ['treadmill', 'juoksumatto']):
                laji = 'Juoksumatto'
            elif any(w in full_text for w in ['indoor_cycling', 'stationary_bike', 'kuntopyora', 'kuntopyörä', 'spinning']):
                laji = 'Kuntopyörä'
            elif any(w in full_text for w in ['rowing', 'row', 'soutu', 'soutulaite']):
                laji = 'Soutu'
            elif any(w in full_text for w in ['crosstraining', 'cross_training', 'crossfit', 'elliptical', 'crosstrainer']):
                laji = 'Crosstraining'
            elif any(w in full_text for w in ['circuit', 'kuntopiiri', 'kuntopiiriharjoittelu']):
                laji = 'Kuntopiiriharjoittelu'
            elif any(w in full_text for w in ['snowboarding', 'snowboard', 'lumilautailu', 'lauta']):
                laji = 'Lumilautailu'
            elif any(w in full_text for w in ['golf']):
                laji = 'Golf'
            elif any(w in full_text for w in ['skating', 'luistelu', 'ice_skating', 'skate']):
                laji = 'Luistelu'
            elif any(w in full_text for w in ['hockey', 'jaakiekko', 'jääkiekko', 'ice_hockey', 'kiekko']):
                laji = 'Jääkiekko'
            elif any(w in full_text for w in ['ski', 'hiihto', 'xc_skiing', 'crosscountry', 'maastohiihto']):
                laji = 'Maastohiihto'
            elif any(w in full_text for w in ['padel', 'tennis', 'racket', 'squash']):
                laji = 'Padel'
            elif any(w in full_text for w in ['gym', 'sali', 'kuntosali', 'weight', 'strength', 'voimailu', 'fitness']):
                laji = 'Kuntosali'
            elif any(w in full_text for w in ['cycling', 'bike', 'pyoraily', 'pyöräily', 'biking']):
                laji = 'Pyöräily'
            elif any(w in full_text for w in ['running', 'run', 'juoksu']):
                laji = 'Juoksu'
            elif any(w in full_text for w in ['walking', 'walk', 'kavely', 'kävely', 'hiking']):
                laji = 'Kävely'
            else:
                laji = 'Muu laji'

            data = []
            vo2max_val = None
            
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        hr = None
                        for ext_elem in point.extensions:
                            for child in ext_elem:
                                tag_lower = child.tag.lower()
                                if tag_lower.endswith('hr'):
                                    try: hr = int(child.text)
                                    except: pass
                                if 'vo2' in tag_lower or 'vo2max' in tag_lower:
                                    try: vo2max_val = float(child.text)
                                    except: pass
                        
                        data.append({
                            'time': point.time,
                            'elevation': point.elevation,
                            'hr': hr
                        })
            
            df_points = pd.DataFrame(data)

            dist_km = gpx.length_2d() / 1000.0 if gpx.length_2d() else 0.0
            
            if not df_points.empty and df_points['time'].notnull().any():
                start_time = df_points['time'].min()
                end_time = df_points['time'].max()
                duration_min = (end_time - start_time).total_seconds() / 60.0 if start_time and end_time else 0.0
                avg_hr = df_points['hr'].mean() if 'hr' in df_points and df_points['hr'].notnull().any() else None
                max_hr = df_points['hr'].max() if 'hr' in df_points and df_points['hr'].notnull().any() else None
            else:
                start_time = gpx.time if gpx.time else None
                duration_min = 0.0
                avg_hr = None
                max_hr = None

            speed_kmh = (dist_km / (duration_min / 60.0)) if duration_min > 0 else 0.0

            calories = None
            if avg_hr and duration_min > 0:
                cal_per_min = (-55.0969 + (36 * 0.2017) - (88 * 0.09036) + (avg_hr * 0.6309)) / 4.184
                if cal_per_min > 0:
                    calories = round(cal_per_min * duration_min, 0)
            elif duration_min > 0:
                met_values = {
                    'Juoksu': 10, 'Juoksumatto': 10, 'Jääkiekko': 9, 'Luistelu': 8, 
                    'Maastohiihto': 9, 'Pyöräily': 8, 'Kuntopyörä': 7, 'Kävely': 4, 
                    'Padel': 7, 'Golf': 4, 'Kuntosali': 5, 'Kuntopiiriharjoittelu': 6, 
                    'Soutu': 7, 'Crosstraining': 8, 'Lumilautailu': 6
                }
                met = met_values.get(laji, 5)
                calories = round((met * 3.5 * 88 / 200) * duration_min, 0)
            else:
                calories = 0

            records.append({
                'Tiedosto': fname,
                'Urheilija': juoksijan_nimi,
                'Päivämäärä': start_time.date() if start_time else None,
                'Aika': start_time if start_time else None,
                'Vuosi': start_time.year if start_time else 2026,
                'Laji': laji,
                'Matka (km)': round(dist_km, 2),
                'Kesto (min)': round(duration_min, 1),
                'Keskinopeus (km/h)': round(speed_kmh, 1),
                'Keskisyke': round(avg_hr, 0) if avg_hr else None,
                'Maksimisyke': round(max_hr, 0) if max_hr else None,
                'VO2Max': vo2max_val,
                'Kalorit (kcal)': calories
            })
        except Exception:
            continue
            
    return pd.DataFrame(records)

df = load_all_gpx("data")

if not df.empty:
    df['Päivämäärä'] = pd.to_datetime(df['Päivämäärä'])
    
    st.subheader("📊 Harjoitusten Yhteenveto & Maksimit")
    
    col_tot1, col_tot2, col_tot3, col_tot4 = st.columns(4)
    col_tot1.metric("Kaikki treenit yhteensä", f"{len(df)} kpl")
    col_tot2.metric("Aikaa urheiltu", f"{round(df['Kesto (min)'].sum() / 60, 1)} h")
    col_tot3.metric("Kokonaiskilometrit", f"{round(df['Matka (km)'].sum(), 1)} km")
    
    tot_cal = int(df['Kalorit (kcal)'].sum()) if df['Kalorit (kcal)'].notnull().any() else 0
    col_tot4.metric("Kokonaiskalorit", f"{tot_cal:,} kcal".replace(",", " "))

    st.write("---")
    
    # --- HELSINKI - BUDAPEST HAASTE ---
    st.subheader("🗺️ Helsinki ➔ Budapest Juoksu & Kävelyhaaste")
    
    TARGET_DIST_KM = 2150.0
    run_walk_df = df[df['Laji'].isin(['Juoksu', 'Juoksumatto', 'Kävely'])].copy()
    current_dist = run_walk_df['Matka (km)'].sum()
    remaining_dist = max(0.0, TARGET_DIST_KM - current_dist)
    progress_pct = min(100.0, (current_dist / TARGET_DIST_KM) * 100)
    
    col_h1, col_h2, col_h3 = st.columns(3)
    col_h1.metric("Kuljettu matka (Juoksu, Juoksumatto & Kävely)", f"{round(current_dist, 1)} km")
    col_h2.metric("Matkaa jäljellä Budapestiin", f"{round(remaining_dist, 1)} km")
    col_h3.metric("Urakasta suoritettu", f"{round(progress_pct, 1)} %")
    
    st.progress(progress_pct / 100)

    if not run_walk_df.empty:
        run_walk_sorted = run_walk_df.dropna(subset=['Päivämäärä']).sort_values('Päivämäärä')
        run_walk_sorted['Kertymä (km)'] = run_walk_sorted['Matka (km)'].cumsum()
        
        fig_budapest = px.line(
            run_walk_sorted,
            x='Päivämäärä',
            y='Kertymä (km)',
            title="Matkan kertyminen kohti Budapestia (2150 km)",
            markers=True
        )
        fig_budapest.add_hline(y=TARGET_DIST_KM, line_dash="dash", line_color="red", annotation_text="Budapest (2150 km)")
        fig_budapest.update_layout(template="plotly_white")
        st.plotly_chart(fig_budapest, use_container_width=True)

    st.write("---")

    # --- VO2 MAX KEHITYS ---
    st.subheader("🫁 VO2 Max -Kuntoindeksin Kehitys")
    df_vo2 = df.dropna(subset=['VO2Max']).sort_values('Päivämäärä')
    
    if not df_vo2.empty:
        fig_vo2 = px.line(
            df_vo2, 
            x='Päivämäärä', 
            y='VO2Max', 
            title="VO2 Max kehitys ajan kuluessa",
            markers=True,
            color='Laji'
        )
        fig_vo2.update_layout(template="plotly_white", yaxis_title="VO2 Max (ml/kg/min)")
        st.plotly_chart(fig_vo2, use_container_width=True)
    else:
        st.info("💡 Sykekello/Sports Tracker ei ole tallentanut VO2Max-arvoa suoraan GPX-laajennukseen.")

    st.write("---")
    
    # --- LAJIKORTIT ---
    st.subheader("🔥 Lajikohtaiset kortit ja maksimitulokset")
    
    unique_sports = df['Laji'].unique()
    
    if len(unique_sports) > 0:
        for sport in sorted(unique_sports):
            sport_df = df[df['Laji'] == sport]
            icon = SPORT_ICONS.get(sport, '🎯')
            
            with st.expander(f"{icon} **{sport}** — {len(sport_df)} harjoitusta", expanded=True):
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
    st.subheader("📋 Kaikki treenit listattuna")
    st.dataframe(df.sort_values("Päivämäärä", ascending=False), use_container_width=True)

else:
    st.info("Kansiossa 'data/' ei ole vielä GPX-tiedostoja tai lataus on kesken.")

else:
    st.info("Kansiossa 'data/' ei ole vielä GPX-tiedostoja tai lataus on kesken.")
