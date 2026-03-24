# =================================================================
# 🟧  — TOULOUSE
# =================================================================

import streamlit as st
import plotly.express as px
import pandas as pd
import geopandas as gpd
import folium
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
df_join = pd.merge(df, df_communes, on="code_insee", how="inner" )
#jointure de soins et communes
df_soin_communes = pd.merge(df_soin, df_communes, on="code_insee", how="inner")

#Sélectionne uniquement les données de la métropole de Toulouse
df_toulouse = df_join[df_join['epci_nom'] == 'Toulouse Métropole']
df_soin_toulouse = df_soin_communes[df_soin_communes['epci_nom'] == 'Toulouse Métropole']

# ─── ONGLET PRINCIPAL ─────────────────────────────────────────────
tab1, tab2, tab3, tab4,  tab5 = st.tabs([ "🏥 Vue d’ensemble", "📍 Carte des Établissements", "🩺 Soins",  "🚑 Distances aux urgences", "🏠 Social et médico-social"
])

# =================================================================
# 🟦 ONGLET 1 — KPI + TYPOLOGIES
# =================================================================

with tab1:
    st.header("Métropôle de Toulouse")
    df_communes_met_toulouse = df_communes_occitanie[df_communes_occitanie['epci_nom'] == 'Toulouse Métropole']
    print('Population de la métropole de Toulouse :', df_communes_met_toulouse['population'].sum())
    # --- KPI ---
    total_etabs = df_toulouse['numero_finess_etablissement'].nunique()
    nb_types = df_toulouse['type d etablissements'].nunique()
    nb_communes = df_communes_met_toulouse['nom_standard'].nunique()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Établissements recensés", f"{total_etabs}")
    col2.metric("Types d’établissements", f"{nb_types}")
    col3.metric("Communes couvertes", f"{nb_communes}")
    col4.metric("Nb de personnes par établissement", f"{df_communes_met_toulouse['population'].sum()/df_toulouse['numero_finess_etablissement'].nunique(): .0f}")
    st.subheader("Typologie des établissements de Toulouse")
    table_typo = (
        df_toulouse.groupby('type d etablissements')
        .agg(nb_etablissements=('numero_finess_etablissement', 'count'))
        .reset_index()
    )
    table_typo['pourcentage'] = (table_typo['nb_etablissements'] / total_etabs * 100).round(2)
    table_typo = table_typo.sort_values('nb_etablissements', ascending=False)
    st.dataframe(table_typo, use_container_width=True, hide_index=True)
    fig_typo = px.bar(
        table_typo,
        x='type d etablissements',
        y='nb_etablissements',
        title="Nombre d'établissements par typologie",
        labels={'type d etablissements': 'Typologie', 'nb_etablissements': 'Nombre'},
    )
    st.plotly_chart(fig_typo, use_container_width=True)
#carte filtres

with tab2:
    groupes_toulouse = sorted(df_toulouse['type d etablissements'].dropna().unique())
    communes = sorted(df_toulouse['nom_standard'].dropna().unique())
    option_tous_groupes_toulouse = "Tous les types"
    option_toutes_communes = "Toutes les communes"
    selection_groupes = st.multiselect(
        "Sélectionner un ou plusieurs types d'établissements :",
        [option_tous_groupes_toulouse] + groupes_toulouse,
        default=[option_tous_groupes_toulouse],
        key="filtre_groupes_toulouse"
    )
    selection_communes = st.multiselect(
        "Sélectionner une ou plusieurs communes :",
        [option_toutes_communes] + communes,
        default=[option_toutes_communes],
        key="filtre_communes"
    )
    df_filtre_toulouse = df_toulouse.copy()
    if option_tous_groupes_toulouse not in selection_groupes:
        df_filtre_toulouse = df_filtre_toulouse[df_filtre_toulouse['type d etablissements'].isin(selection_groupes)]
    if option_toutes_communes not in selection_communes:
        df_filtre_toulouse = df_filtre_toulouse[df_filtre_toulouse['nom_standard'].isin(selection_communes)]
        # Centre de la carte
    center_lat = 43.6045
    center_lon = 1.4440
    zoom_level = 10   # 👉 Ajuste ici (12 = ville, 13 = centre, 14 = rues)
    fig = px.scatter_mapbox(
        df_filtre_toulouse,
        lat="latitude",
        lon="longitude",
        hover_name="raison_sociale",
        hover_data={"type d etablissements": True},
        color="type d etablissements",
        zoom=zoom_level,        # 👉 Utilisation du zoom dynamique
        height=650
    )
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_center={"lat": center_lat, "lon": center_lon},  # 👉 Centre réel
        margin={"r":0, "t":0, "l":0, "b":0}
    )
    st.plotly_chart(fig, use_container_width=True)

# =================================================================
# 🟧 ONGLET 3 — CARTE PAR TYPE DE SOIN
# =================================================================
with tab3:
    st.header("Carte interactive des soins de santé")
    
    
    # --- KPI ---
    total_soins = df_soin_toulouse['libactivite'].notna().sum()
    

    col1, col2, col3 = st.columns(3)
    col1.metric("Nombre d'Établissements de soins recensés", f"{total_soins}")
    
 #carte
        # --- Listes pour les filtres ---
    groupes_soin_toulouse = sorted(df_soin_toulouse['groupe_activites'].dropna().unique())
    communes = sorted(df_toulouse['nom_standard'].dropna().unique())

    option_tous_groupes_toulouse = "Tous les types"
    option_toutes_communes = "Toutes les communes"

    # --- Widgets Streamlit ---
    selection_groupes = st.multiselect(
        "Sélectionner un ou plusieurs types d'établissements :",
        [option_tous_groupes_toulouse] + groupes_soin_toulouse,
        default=[option_tous_groupes_toulouse],
        key="filtre_groupes_soin_toulouse"
    )

    selection_communes = st.multiselect(
        "Sélectionner une ou plusieurs communes :",
        [option_toutes_communes] + communes,
        default=[option_toutes_communes],
        key="filtre_soins_communes"
    )

    # --- Application des filtres ---
    df_filtre_soin_toulouse = df_soin_toulouse.copy()

    if option_tous_groupes_toulouse not in selection_groupes:
        df_filtre_soin_toulouse = df_filtre_soin_toulouse[
            df_filtre_soin_toulouse['groupe_activites'].isin(selection_groupes)
        ]

    if option_toutes_communes not in selection_communes:
        df_filtre_soin_toulouse = df_filtre_soin_toulouse[
            df_filtre_soin_toulouse['nom_standard'].isin(selection_communes)
        ]

    # --- Carte ---
    center_lat = 43.6045
    center_lon = 1.4440
    zoom_level = 10

    fig = px.scatter_mapbox(
        df_filtre_soin_toulouse,
        lat="latitude",
        lon="longitude",
        hover_name="raison_sociale",
        hover_data={"groupe_activites": True},
        color="groupe_activites",
        zoom=zoom_level,
        height=650
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_center={"lat": center_lat, "lon": center_lon},
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    st.plotly_chart(fig, use_container_width=True)