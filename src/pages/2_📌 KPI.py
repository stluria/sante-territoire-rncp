import streamlit as st
import plotly.express as px
import pandas as pd
import geopandas as gpd
import folium
#from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from pathlib import Path
from streamlit_folium import st_folium

# ─── CHARGEMENT DONNÉES ───────────────────────────────────────────

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE_DIR,"..", "data", "etablissements_occitanie.csv"), sep=';',dtype={"departement": str})
df_communes = pd.read_csv(os.path.join(BASE_DIR,"..", "data","communes-france-2025.csv"), sep=",", encoding="utf-8")
df_communes_occitanie = df_communes[df_communes['reg_nom'] == 'Occitanie']
df_soin = pd.read_csv(os.path.join(BASE_DIR,"..", "data","soins_limit.csv"), sep=';', encoding="utf-8")
df_urgences = df_soin[df_soin['libactivite'].str.contains("urgence", case=False, na=False)]
df_distances = pd.read_csv(os.path.join(BASE_DIR,"..", "data","distances_communes_urgence_occitanie.csv"))


# =================================================================
# 🟦 PAGE — KPI + TYPOLOGIES
# =================================================================

st.header("🏥 Les principaux indicateurs des établissements de santé en Occitanie")
# --- KPI de base ---
total_etabs = df['numero_finess_etablissement'].nunique()
nb_types = df['type d etablissements'].nunique()
nb_deps = df['departement'].nunique()
population_occitanie = df_communes_occitanie['population'].sum()
habitants_par_etab = population_occitanie / total_etabs
st.subheader("📌 Vue d’ensemble")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Établissements recensés", f"{total_etabs}")
col2.metric("Population (millions)", "6.1")
col3.metric("Départements couverts", f"{nb_deps}")
col4.metric("Habitants par établissement", f"{habitants_par_etab:,.0f}")
# --- KPI comparatifs France ---
st.subheader("📊 Mise en perspective nationale")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Part des établissements français", f"{round(total_etabs/102553*100, 2)} %")
col2.metric("Part de la population française", "9 %")
col3.metric("Départements en France", "106")
col4.metric("Habitants/établissement (France)", "673")
st.markdown(
    """
    ### 🧭 Interprétation  
    L’Occitanie apparaît comme un territoire **bien doté en établissements de santé**, 
    avec un ratio habitants/établissement plus favorable que la moyenne nationale.
    """
)
# --- Typologie des établissements ---
st.subheader("🏷️ Répartition par typologie")
table_typo = (
    df.groupby('type d etablissements')
      .agg(nb_etablissements=('numero_finess_etablissement', 'count'))
      .reset_index()
)
table_typo['pourcentage'] = (table_typo['nb_etablissements'] / total_etabs * 100).round(2)
table_typo = table_typo.sort_values('nb_etablissements', ascending=False)
fig_typo = px.bar(
    table_typo,
    x='type d etablissements',
    y='nb_etablissements',
    title="Nombre d'établissements par typologie",
    labels={'type d etablissements': 'Typologie', 'nb_etablissements': 'Nombre'},
    color='nb_etablissements',
    color_continuous_scale='Blues'
)
st.plotly_chart(fig_typo, use_container_width=True, key="fig_typo")
# --- Distances aux urgences ---
st.header("🚑 Analyse des distances aux services d’urgences")
df_dist = df_distances.copy()
distance_moyenne = df_dist["distance_urgence_km"].mean()
distance_max = df_dist["distance_urgence_km"].max()
col1, col2 = st.columns(2)
col1.metric("Distance moyenne", f"{distance_moyenne:.1f} km")
col2.metric("Distance maximale", f"{distance_max:.1f} km")
st.subheader("📍 Distance moyenne selon la densité de population")
distance_par_dep = (
    df_dist
    .groupby('grille_densite_texte')['distance_urgence_km']
    .mean()
    .reset_index()
    .sort_values('distance_urgence_km', ascending=False)
)
st.dataframe(distance_par_dep, use_container_width=True, hide_index=True)
st.markdown(
    """
    ### 🔎 Points clés  
    - Le seuil critique de **30 minutes d’accès** est un repère important en santé publique.  
    - Les zones **rurales** sont les plus exposées à un risque d’éloignement des services d’urgence.  
    - Cette analyse permet d’identifier les territoires où un renforcement de l’offre pourrait être prioritaire.
    """
)
st.header("Carte des communes et des centres d’urgence")
# --- Carte Plotly ---
fig = px.scatter_map(
    df_distances,
    lat="latitude_centre",
    lon="longitude_centre",
    hover_name="nom_standard",
    hover_data={"dep_nom": True, "distance_urgence_km": True},
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
st.plotly_chart(fig, use_container_width=True)

