import streamlit as st
import plotly.express as px
import pandas as pd
import geopandas as gpd
import folium
import numpy as np
#from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from pathlib import Path
from streamlit_folium import st_folium

# ─── CHARGEMENT DONNÉES ───────────────────────────────────────────
df = pd.read_csv("data/etablissements_occitanie.csv", sep=';',dtype={"departement": str, "code_insee": str})
df_communes = pd.read_csv("data/communes-france-2025.csv", sep=",", encoding="utf-8",   dtype={"departement": str, "code_insee": str}
)
df_communes_occitanie = df_communes[df_communes['reg_nom'] == 'Occitanie']
df_soin = pd.read_csv("data/soins_limit.csv", sep=';', encoding="utf-8", dtype={"departement": str,"code_insee": str})
df_urgences = df_soin[df_soin['libactivite'].str.contains("urgence", case=False, na=False)]
df_distances = pd.read_csv("data/distances_communes_urgence_occitanie.csv")
df_equipements = pd.read_csv("data/equipements_occitanie.csv", sep=';', encoding="utf-8", dtype={"departement": str,"code_insee": str})
df_join = pd.merge(df, df_communes, on="code_insee", how="left" )
#jointure de soins et communes
df_soin_communes = pd.merge(df_soin, df_communes, on="code_insee", how="inner")

# --- CONFIGURATION ---
st.set_page_config(page_title="Offres de soins - Occitanie", layout="wide")

# ─── ONGLET PRINCIPAL ─────────────────────────────────────────────
tab3, tab4 = st.tabs([ "🩺 Soins",  "🚑 Distances aux urgences"
])
# =================================================================
# 🟧 ONGLET 3 — CARTE PAR TYPE DE SOIN
# =================================================================
with tab3:
    st.header("Carte interactive des soins de santé")
    
    departements_occitanie = ["09","11", "12", "30","31", "32", "34", "46", "48","65", "66", "81", "82",  ]
    df_soin_occitanie = df_soin[df_soin["departement"].isin(departements_occitanie)]
    # --- KPI ---
    total_soins = df_soin_occitanie['libactivite'].notna().sum()
    moyenne = round(df_soin_occitanie['libactivite'].notna().sum()/df_soin_occitanie['numero_finess_etablissement'].nunique(),2)
    

    col1, col2, col3 = st.columns(3)
    col1.metric("Nombre de prestations de soins recensées", f"{total_soins}")
    col2.metric("Nombre moyen de soins par établissement", f"{moyenne}")
    
    df_filtre2 = df_soin_occitanie.copy()
    df_filtre2["libactivite_short"] = df_filtre2["libactivite"].str.slice(0, 20) + "…"

    soins = sorted(df_filtre2['libactivite_short'].dropna().unique())
    departements2 = sorted(df_filtre2['departement'].dropna().unique())
    

    option_tous_soins = "Tous les soins"
    option_tous_deps2 = "Tous les départements"

    selection_soins = st.multiselect(
        "Sélectionner un ou plusieurs soins :",
        [option_tous_soins] + soins,
        default=[option_tous_soins],
        key="filtre_soins"
    )

    selection_deps2 = st.multiselect(
        "Sélectionner un ou plusieurs départements :",
        [option_tous_deps2] + departements2,
        default=[option_tous_deps2],
        key="filtre_departements_soins"
    )



    if option_tous_soins not in selection_soins:
        df_filtre2 = df_filtre2[df_filtre2['libactivite_short'
        ''].isin(selection_soins)]

    if option_tous_deps2 not in selection_deps2:
        df_filtre2 = df_filtre2[df_filtre2['departement'].isin(selection_deps2)]

    if not df_filtre2.empty:
        center_lat = df_filtre2['latitude'].mean()
        center_lon = df_filtre2['longitude'].mean()
    else:
        center_lat, center_lon = 46.5, 2.5

    fig2 = px.scatter_map(
        df_filtre2,
        lat="latitude",
        lon="longitude",
        hover_name="raison_sociale",
        hover_data={"libforme": True},
        color="libactivite_short",
        zoom=6,
        height=650,
        width=1200
    )

    fig2.update_layout(
        map_style="open-street-map",
        map_center={"lat": center_lat, "lon": center_lon},
        margin={"r":0, "t":0, "l":0, "b":0}
    )

    st.plotly_chart(fig2, use_container_width=True)


    #-- radar ---
    
    
    
    # --- Fonction haversine (distance en km) ---
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        lat1, lon1 = np.radians(lat1), np.radians(lon1)
        lat2, lon2 = np.radians(lat2), np.radians(lon2)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
        return 2 * R * np.arcsin(np.sqrt(a))
    
    
    st.subheader("🧭 Radar des distances moyennes aux types de soins (Occitanie)")
    
    # --- Liste des EPCI disponibles ---
    liste_epci = ["Tous Occitanie"] + sorted(df_communes_occitanie["epci_nom"].dropna().unique())
    
    # --- Sélecteur EPCI ---
    epci_selection = st.selectbox("Filtrer par EPCI :", liste_epci)
    
    # --- On garde une copie de base pour Occitanie entière ---
    df_occ_base = df_communes_occitanie.copy()
    
    # --- Filtrage des communes selon EPCI ---
    if epci_selection != "Tous Occitanie":
        df_communes_filtre = df_occ_base[df_occ_base["epci_nom"] == epci_selection]
    else:
        df_communes_filtre = df_occ_base
    
    df_communes_filtre = df_communes_filtre[[
        "code_insee", "nom_standard", "latitude_centre", "longitude_centre"
    ]].dropna()
    
    # --- Nettoyage des soins ---
    df_soins = df_soin.dropna(subset=["latitude", "longitude", "groupe_activites"]).copy()
    
    types_soins = df_soins["groupe_activites"].unique()
    
    # --- Fonction générique pour calculer les distances moyennes ---
    def calculer_radar(df_communes_zone):
        resultats = []
    
        for type_soin in types_soins:
            df_type = df_soins[df_soins["groupe_activites"] == type_soin]
    
            etab_lats = df_type["latitude"].values
            etab_lons = df_type["longitude"].values
    
            distances_min = []
    
            for idx, com in df_communes_zone.iterrows():
                lat_c = com["latitude_centre"]
                lon_c = com["longitude_centre"]
    
                d = haversine(lat_c, lon_c, etab_lats, etab_lons)
                distances_min.append(d.min())
    
            resultats.append({
                "groupe_activites": type_soin,
                "distance_moyenne_km": np.mean(distances_min)
            })
    
        df_res = pd.DataFrame(resultats)
        df_res["distance_moyenne_km"] = df_res["distance_moyenne_km"].round(2)
        return df_res
    
    # --- 1) Occitanie entière ---
    df_radar_occ = calculer_radar(df_occ_base)
    df_radar_occ["zone"] = "Occitanie"
    
    # --- 2) Toulouse Métropole ---
    df_tm = df_occ_base[df_occ_base["epci_nom"] == "Toulouse Métropole"]
    df_radar_tm = calculer_radar(df_tm)
    df_radar_tm["zone"] = "Toulouse Métropole"
    
    # --- 3) EPCI sélectionné ---
    df_radar_sel = calculer_radar(df_communes_filtre)
    df_radar_sel["zone"] = epci_selection
    
    # --- Fusion ---
    df_radar_all = pd.concat([df_radar_occ, df_radar_tm, df_radar_sel])
    
    # --- Tableau ---
    st.dataframe(
        df_radar_sel.sort_values("distance_moyenne_km", ascending=False),
        use_container_width=True
    )
    
    # --- Radar Plotly multi-traces ---
    fig = px.line_polar(
        df_radar_all,
        r="distance_moyenne_km",
        theta="groupe_activites",
        color="zone",
        line_close=True,
        title=f"Radar des distances moyennes aux soins : {epci_selection} vs Occitanie vs Toulouse Métropole"
    )
    fig.update_traces(fill="toself")
    
    st.plotly_chart(fig, use_container_width=True)
    
    
# =================================================================
# 🟧 ONGLET 4 — SERVICES D URGENCE
# =================================================================

with tab4:
    st.header("Distance aux services d’urgence")

    # Charger les distances calculées dans le notebook
    df_dist = df_distances.copy()

    # KPI distance moyenne
    distance_moyenne = df_dist["distance_urgence_km"].mean()

    st.metric(
        "Distance moyenne au service d’urgence le plus proche en Occitanie. La distance est calculée à partir du centre de chaque commune par rapport au service d'urgence le plus proche",
        f"{distance_moyenne:.1f} km"
    )
    # Filtrer uniquement sur Toulouse Métropole et CC Pyrénées Audoises
    epci_cibles = ["Toulouse Métropole", "CC Pyrénées Audoises"]

    df_filtre_dist = df_dist[df_dist["epci_nom"].isin(epci_cibles)].copy()
    df_communes_filtrees = df_communes_occitanie[df_communes_occitanie["epci_nom"].isin(epci_cibles)].copy()

    

   
##nouveau code 

        # --- Calcul distance moyenne par EPCI ---
    table_distances = (
        df_filtre_dist.groupby("epci_nom")
        .agg(
            distance_moyenne_km=("distance_urgence_km", "mean"),
            nb_communes=("code_insee", "count")
        )
        .reset_index()
    )

    # Arrondir pour lisibilité
    table_distances["distance_moyenne_km"] = table_distances["distance_moyenne_km"].round(2)

    # --- Affichage ---
    st.dataframe(table_distances, use_container_width=True)



    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distance moyenne par département - Worst 5")
    # Distance moyenne par département
        
        distance_par_dep = (
            df_dist
            .groupby('dep_nom')['distance_urgence_km']
            .mean()
            .reset_index()
            .sort_values('distance_urgence_km', ascending=False)
            .head(5)
        )

        st.dataframe(distance_par_dep, use_container_width=True, hide_index=True)
    

    with col2:
        col2.subheader("Distance moyenne par densité de population")
        # Distance moyenne par densité de population
        st.markdown("⚠️ Une même EPCI peut avoir des communes dans différentes catégorie de densité de population")
        distance_par_dep = (
           df_dist 
            .groupby('grille_densite_texte')['distance_urgence_km']
            .mean()
            .reset_index()
            .sort_values('distance_urgence_km', ascending=False)
        )

  
        st.dataframe(distance_par_dep, use_container_width=True, hide_index=True)

    # Mettre un graphique de distribution des distances
    


    # ───────────────────────────────────────────────
    #  Histogramme lissé (density) — sans SciPy
    # ───────────────────────────────────────────────
    st.subheader("Distribution lissée des communes")

    fig_density = px.histogram(
        df_dist,
        x="distance_urgence_km",
        nbins=40,
        histnorm="density",
        opacity=0.6,
        title="Distribution lissée des distances aux urgences par commune",
        labels={"distance_urgence_km": "Distance (km)"},
        marginal="box"  # ajoute un boxplot au-dessus
    )

    st.plotly_chart(fig_density, use_container_width=True)

    st.header("Carte des communes et des centres d’urgence")

    # --- Carte Plotly ---
    fig = px.scatter_map(
        df_distances,
        lat="latitude_centre",
        lon="longitude_centre",
        hover_name="nom_standard",
        hover_data={"dep_nom": True, "distance_urgence_km": True, "epci_nom": True},
        color="distance_urgence_km",   # 🔥 coloration selon la distance
        color_continuous_scale="Viridis",  # ou "Turbo", "Plasma", "Inferno"

        zoom=6,
        height=700
    )

    # Ajouter les centres d’urgence en rouge
    fig.add_scattermap(
        lat=df_urgences["latitude"],
        lon=df_urgences["longitude"],
        mode="markers",
        marker=dict(size=10, color="red"),
        name="Centres d'urgence",
        hovertext=df_urgences["raison_sociale"]
    )

    fig.update_layout(
        map_style="open-street-map",
        margin={"r":0, "t":0, "l":0, "b":0}
    )

    st.plotly_chart(fig, use_container_width=True, key=2)
