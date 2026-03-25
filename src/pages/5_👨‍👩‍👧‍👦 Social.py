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
st.set_page_config(page_title="Les prestations sociales - Occitanie", layout="wide")



# =================================================================
# 🟧 ONGLET - PRESTATIONS SOCIALES
# =================================================================
# 2. INDICATEURS CLÉS
# ───────────────────────────────────────────────

st.header("Indicateurs clés des prestations sociales et médico-sociales")
st.markdown("""### Il faut noter qu'un même établissement peut proposer plusieurs prestations sociales""")
col1, col2, col3 = st.columns(3)
col1.metric("Nombre total de prestations proposées", len(df_equipements))
if "type_equipement" in df.columns:
    col2.metric("Types de prestations recensés", df_equipements["type_equipement"].nunique())
if "departement" in df.columns:
    col3.metric("Départements couverts", df_equipements["departement"].nunique())
# ───────────────────────────────────────────────
# 3. FILTRES
# ───────────────────────────────────────────────
# Départements
st.markdown("### Filtrez vos données: (le filtre s'applique sur tous les graphiques suivants)")
if "libdepartement" in df_equipements.columns:
    departements = sorted(df_equipements["libdepartement"].dropna().unique())
    selected_dep = st.selectbox("Département :", ["Tous"] + departements)
else:
    selected_dep = "Tous"
# Types d'équipement
if "groupe_equipement" in df_equipements.columns:
    types = sorted(df_equipements["groupe_equipement"].dropna().unique())
    selected_type = st.selectbox("Type d'équipements groupés :", ["Tous"] + types)
else:
    selected_type = "Tous"
# Application des filtres
df_filtered = df_equipements.copy()
if selected_dep != "Tous":
    df_filtered = df_filtered[df_filtered["libdepartement"] == selected_dep]
if selected_type != "Tous":
    df_filtered = df_filtered[df_filtered["groupe_equipement"] == selected_type]
st.write(f"Nombre de prestations après filtre : {len(df_filtered)}")
# ───────────────────────────────────────────────
# 4. RÉPARTITION PAR DÉPARTEMENT
# ───────────────────────────────────────────────


import plotly.express as px
st.header("Nombre de prestations par département et par type")
if "libdepartement" in df_filtered.columns and "groupe_equipement" in df_filtered.columns:
    
    # Regroupement
    df_group = (
        df_filtered
        .groupby(["libdepartement", "groupe_equipement"])
        .size()
        .reset_index(name="Nombre")
    )

    # Supprimer les lignes vides
    df_group = df_group[df_group["Nombre"] > 0]

    # Graphique horizontal groupé
    fig = px.bar(
        df_group,
        x="Nombre",
        y="libdepartement",
        color="groupe_equipement",
        orientation="h",
        title="Équipements par département et par type",
        labels={
            "libdepartement": "Département",
            "Nombre": "Nombre de prestations",
            "groupe_equipement": "Type de prestation"
            }
        )
    
    fig.update_layout(barmode="stack", height=700)
    st.plotly_chart(fig, use_container_width=True)
    

    # ───────────────────────────────────────────────
    # 5. RÉPARTITION PAR TYPE D'ÉQUIPEMENT
    # ───────────────────────────────────────────────
    st.header("Répartition par type de prestations")

    if "groupe_equipement" in df_equipements.columns:
        df_type = df_filtered.groupby("groupe_equipement").size().reset_index(name="count")

        fig_type = px.treemap(
            df_type,
            path=["groupe_equipement"],
            values="count",
            title="Répartition des prestations par type"
        )
        st.plotly_chart(fig_type, use_container_width=True)

    # ───────────────────────────────────────────────
    # 6. CARTE INTERACTIVE
    # ───────────────────────────────────────────────
    st.header("Carte des prestations")

    if "latitude" in df_filtered.columns and "longitude" in df_filtered.columns:

        fig_map = px.scatter_mapbox(
            df_filtered,
            lat="latitude",
            lon="longitude",
            hover_name="nom_etablissement" if "nom_etablissement" in df_filtered.columns else None,
            hover_data={
                "libde_equipement": "libde_equipement" in df_filtered.columns,
                "groupe_equipement": "groupe_equipement" in df_filtered.columns,
                "rslongue": "rslongue" in df_filtered.columns,
                "commune" : "commune" in df_filtered.columns
            },
            color="groupe_equipement" if "groupe_equipement" in df_filtered.columns else None,
            zoom=6,
            height=650
        )


    #if "latitude" in df.columns and "longitude" in df_equipements.columns:
    #    fig_map = px.scatter_mapbox(
    #        df_filtered,
    #        lat="latitude",
    #        lon="longitude",
    #        hover_name="nom_etablissement" if "nom_etablissement" in df.columns else None,
    #        hover_data={"type d etablissements": True, "libde_equipement": True, "groupe_equipement": True},
    #        color="groupe_equipement" if "groupe_equipement" in df.columns else None,
    #        zoom=6,
    #        height=650
    #    )

        fig_map.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0, "t":0, "l":0, "b":0}
        )

        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("Aucune coordonnée géographique disponible pour afficher la carte.")
