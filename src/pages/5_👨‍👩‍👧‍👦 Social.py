import streamlit as st
import plotly.express as px
import pandas as pd
import geopandas as gpd
import folium
import numpy as np
#from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from pathlib import Path
from streamlit_folium import st_folium
import altair as alt
import json




import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE_DIR,"..", "data", "etablissements_occitanie.csv"), sep=';',dtype={"departement": str})
df_communes = pd.read_csv(os.path.join(BASE_DIR,"..", "data","communes-france-2025.csv"), sep=",", encoding="utf-8")
df_communes_occitanie = df_communes[df_communes['reg_nom'] == 'Occitanie']
df_soin = pd.read_csv(os.path.join(BASE_DIR,"..", "data","soins_limit.csv"), sep=';', encoding="utf-8")
df_urgences = df_soin[df_soin['libactivite'].str.contains("urgence", case=False, na=False)]
df_distances = pd.read_csv(os.path.join(BASE_DIR,"..", "data","distances_communes_urgence_occitanie.csv"))
df_equipements = pd.read_csv(os.path.join(BASE_DIR,"..", "data","equipements_occitanie.csv"), sep=';', encoding="utf-8", dtype={"departement": str,"code_insee": str})
df_join = pd.merge(df, df_communes, on="code_insee", how="left" )
#jointure de soins et communes
df_soin_communes = pd.merge(df_soin, df_communes, on="code_insee", how="inner")# ─── CHARGEMENT DONNÉES ───────────────────────────────────────────

#jointure de soins et communes
df_equipements_communes = pd.merge(df_equipements, df_communes, on="code_insee", how="inner")
#charge la carte
with open("data/epci_occitanie.geojson", encoding="utf-8") as f:
    geojson_epci = json.load(f)
# --- CONFIGURATION ---
st.set_page_config(page_title="Les prestations sociales - Occitanie", layout="wide")

# ─── ONGLET PRINCIPAL ─────────────────────────────────────────────
tab1, tab2 = st.tabs([ "Prestations sociales",  "Capacités"
])

# =================================================================
# 🟧 ONGLET - PRESTATIONS SOCIALES
# =================================================================
# 2. INDICATEURS CLÉS
# ───────────────────────────────────────────────
with tab1 :
    st.header("Indicateurs clés des prestations sociales et médico-sociales")
    st.markdown("""### Il faut noter qu'un même établissement peut proposer plusieurs prestations sociales""")
    col1, col2, col3 = st.columns(3)
    moyenne = round(df_equipements['libde_equipement'].notna().sum()/df_equipements['nofinesset'].nunique(),2)
    col1.metric("Nombre total de prestations proposées", len(df_equipements))
    col2.metric("Nombre moyen de prestation par établissement", f"{moyenne}")
    if "departement" in df.columns:
        col3.metric("Départements couverts", df_equipements["departement"].nunique())
    # ───────────────────────────────────────────────
    # 3. FILTRES
    # ───────────────────────────────────────────────
    # Départements
    st.markdown("### Filtrez vos données: (le filtre s'applique sur tous les graphiques suivants)")
    if "libdepartement" in df_equipements.columns:
        departements = sorted(df_equipements_communes["libdepartement"].dropna().unique())
        selected_dep = st.selectbox("Département :", ["Tous"] + departements)
    else:
        selected_dep = "Tous"
    # Types d'équipement
    if "groupe_equipement" in df_equipements_communes.columns:
        types = sorted(df_equipements_communes["groupe_equipement"].dropna().unique())
        selected_type = st.selectbox("Type d'équipements groupés :", ["Tous"] + types)
    else:
        selected_type = "Tous"



    # Application des filtres
    df_filtered = df_equipements_communes.copy()
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

        # Regroupe_equipementment
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
                hover_name="raison_sociale" if "raison_sociale" in df_filtered.columns else None,
                hover_data={
                    "libde_equipement": "libde_equipement" in df_filtered.columns,
                    "groupe_equipement": "groupe_equipement" in df_filtered.columns,
                    "raison_sociale_longue": "raison_sociale_longue" in df_filtered.columns,
                    "commune" : "commune" in df_filtered.columns,
                    "capinstot": "capinstot" in df_filtered.columns
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
        #        hover_name="raison_sociale" if "raison_sociale" in df.columns else None,
        #        hover_data={"type d etablissements": True, "libde_equipement": True, "groupe_equipement_equipement": True},
        #        color="groupe_equipement_equipement" if "groupe_equipement_equipement" in df.columns else None,
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


# =================================================================
# 🟦 ONGLET - CAPACITÉS D’HÉBERGEMENT
# =================================================================
with tab2:
    st.header("Capacités d’hébergement en Occitanie")
    st.markdown("Analyse des capacités d’accueil des établissements médico‑sociaux.")   

    df_cap = df_equipements.copy()  

    # -----------------------------
    # KPIs
    # -----------------------------
    col1, col2, col3, col4 = st.columns(4)  

    col1.metric("Établissements", df_cap["nofinesset"].nunique())
    col2.metric("Capacité totale", int(df_cap["capinstot"].sum()))
    col3.metric("Capacité moyenne par service", round(df_cap["capinstot"].mean(), 1))
    col4.metric("Capacité nulle", int((df_cap["capinstot"] == 0).sum()))  

    st.divider()    

    # -----------------------------
    # FILTRES
    # -----------------------------
    st.subheader("Filtres") 

    dep_list = sorted(df_equipements_communes["libdepartement"].dropna().unique())
    type_list = sorted(df_equipements_communes["groupe_equipement"].dropna().unique())  
    epci_list = sorted(df_equipements_communes["epci_nom"].dropna().unique())    

    f_dep = st.selectbox("Département :", ["Tous"] + dep_list, key="dep_capacites")
    f_type = st.selectbox("Type d’équipement :", ["Tous"] + type_list, key="equip_capacite") 
    f_epci = st.selectbox("EPCI:", ["Tous"] + epci_list, key="ecpi_capacite" ) 

    df_cap_filtered = df_equipements_communes.copy()
    if f_dep != "Tous":
        df_cap_filtered = df_cap_filtered[df_cap_filtered["libdepartement"] == f_dep]
    if f_type != "Tous":
        df_cap_filtered = df_cap_filtered[df_cap_filtered["groupe_equipement"] == f_type]
    if f_epci != "Tous":
        df_cap_filtered = df_cap_filtered[df_cap_filtered["epci_nom"] == f_epci]

    st.write(f"Établissements après filtre : {len(df_cap_filtered)}")   

    st.divider()    

    

    # -----------------------------
    # CAPACITÉ PAR TYPE D'ÉQUIPEMENT
    # -----------------------------
    st.subheader("🏷️ Capacité totale par type d’équipement")    

    cap_by_type = (
        df_cap_filtered.groupby("libde_equipement")["capinstot"]
        .sum()
        .reset_index()
        .sort_values("capinstot", ascending=False)
    )   

    bar_type = alt.Chart(cap_by_type).mark_bar().encode(
        x=alt.X("capinstot:Q", title="Capacité totale"),
        y=alt.Y("libde_equipement:N", sort="-x", title="Type d’équipement")
    ).properties(height=500)    

    st.altair_chart(bar_type, use_container_width=True) 

    st.divider()    

    # -----------------------------
    # CAPACITÉ PAR DÉPARTEMENT
    # -----------------------------
    st.subheader("📍 Capacité totale par département")  

    cap_by_dep = (
        df_cap_filtered.groupby("libdepartement")["capinstot"]
        .sum()
        .reset_index()
        .sort_values("capinstot", ascending=False)
    )   

    fig_dep = px.bar(
        cap_by_dep,
        x="libdepartement",
        y="capinstot",
        title="Capacité totale par département",
        labels={"libdepartement": "Département", "capinstot": "Capacité totale"}
    )   

    st.plotly_chart(fig_dep, use_container_width=True)  

    st.divider()    

    
    # =================================================================
    # 🟦 CAPACITÉS D’ACCUEIL / POPULATION — ZONES À RISQUE AVEC FILTRES
    # =================================================================

    st.header("Capacités d’accueil rapportées à la population")
    st.markdown("""
    Cet indicateur compare la capacité d’accueil médico-sociale à la population réelle 
    de chaque territoire (EPCI). Il permet d’identifier les zones potentiellement sous-dotées.
    """)

    # -----------------------------
    # 0. FILTRES AVANCÉS
    # -----------------------------
    st.subheader("Filtres")

    # Filtre type d'équipement
    if "groupe_equipement" in df_equipements_communes.columns:
        types = sorted(df_equipements_communes["groupe_equipement"].dropna().unique())
        f_type_risque = st.selectbox(
            "Type d’équipement :", 
            ["Tous"] + types,
            key="type_risque"
        )
    else:
        f_type_risque = "Tous"

    # Filtre client
    if "client" in df_equipements_communes.columns:
        clients = sorted(df_equipements_communes["client"].dropna().unique())
        f_client_risque = st.selectbox(
            "Public visé :", 
            ["Tous"] + clients,
            key="client_risque"
        )
    else:
        f_client_risque = "Tous"

    # Application des filtres
    df_risque_filtered = df_equipements_communes.copy()

    if f_type_risque != "Tous":
        df_risque_filtered = df_risque_filtered[df_risque_filtered["groupe_equipement"] == f_type_risque]

    if f_client_risque != "Tous":
        df_risque_filtered = df_risque_filtered[df_risque_filtered["client"] == f_client_risque]


    # -----------------------------
    # 2. AGRÉGATION PAR EPCI
    # -----------------------------

    # Population par EPCI (depuis df_communes)
    df_pop_epci = (
        df_communes.groupby("epci_nom")
        .agg({"population": "sum"})
        .reset_index()
    )

    # Capacité par EPCI (depuis df_risque_filtered)
    df_cap_epci = (
        df_risque_filtered.groupby("epci_nom")
        .agg({"capinstot": "sum"})
        .reset_index()
    )

    # Fusion population + capacités
    df_epci = df_pop_epci.merge(df_cap_epci, on="epci_nom", how="left")
    df_epci["capinstot"] = df_epci["capinstot"].fillna(0)


    # -----------------------------
    # 3. AJOUT DES EPCI ABSENTS
    # -----------------------------
    geojson_names = [f["properties"]["nom"] for f in geojson_epci["features"]]
    df_epci_complet = pd.DataFrame({"epci_nom": geojson_names})

    df_epci_map = df_epci_complet.merge(df_epci, on="epci_nom", how="left")
    df_epci_map["population"] = df_epci_map["population"].fillna(0)
    df_epci_map["capinstot"] = df_epci_map["capinstot"].fillna(0)

    # Calcul du ratio
    df_epci_map["places_pour_100_habitants"] = (
        (df_epci_map["capinstot"]*100) / (df_epci_map["population"]).replace(0, 1)
    )


    # -----------------------------
    # 4. HISTOGRAMME
    # -----------------------------

     # Récupération du filtre EPCI actif
    filtre_actuel = st.session_state.get("type_risque", "Tous")

    # Construction du texte à afficher
    if filtre_actuel == "Tous":
        titre_filtre = " (Tous équipements)"
    else:
        titre_filtre = f" ({filtre_actuel})"

    # Affichage du titre
    st.subheader("📊 Moyenne" + titre_filtre)

    col1, col2, col3, col4 = st.columns(4)  
    col1.metric("Moyenne de places pour 100 habitants par EPCI", df_epci_map["places_pour_100_habitants"].mean())
    moyenne = df_epci_map["places_pour_100_habitants"].mean()



    # -----------------------------
    # 5. ZONES À RISQUE
    # -----------------------------
    st.subheader("🚨 Zones potentiellement sous-dotées" + titre_filtre)

    seuil = df_epci_map["places_pour_100_habitants"].quantile(0.25)
    zones_risque = df_epci_map[df_epci_map["places_pour_100_habitants"] <= seuil]

    st.markdown(f"**Seuil automatique de risque : {seuil:.4f} soit 25% les moins bien dotés (1er quartile)**")
    st.dataframe(zones_risque, use_container_width=True)


    # =================================================================
    # 🗺️ CARTE DES ZONES SOUS-DOTÉES (EPCI)
    # =================================================================

    st.subheader("🗺️ Carte des zones potentiellement sous-dotées")

    fig_map = px.choropleth_mapbox(
        df_epci_map,
        geojson=geojson_epci,
        locations="epci_nom",
        featureidkey="properties.nom",
        color="places_pour_100_habitants",
        color_continuous_scale="Reds_r",
        mapbox_style="carto-positron",
        zoom=6,
        center={"lat": 43.6, "lon": 2.2},
        opacity=0.7,
        hover_data={
            "capinstot": True,
            "population": True,
            "places_pour_100_habitants": ":.4f"
        }
    )

    st.plotly_chart(fig_map, use_container_width=True)