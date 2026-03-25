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


# On essaie d'utiliser __file__, sinon on prend le dossier actuel
try:
    BASE_DIR = Path(__file__).resolve().parent
except NameError:
    BASE_DIR = Path.cwd()

ROOT = BASE_DIR.parent
DATA_DIR = ROOT / "data"


# --- CONFIGURATION ---
st.set_page_config(page_title="L'établissements de santé - Occitanie", layout="wide")

# --- CHARGEMENT DES DONNÉES ---
# Assurez-vous que df_geom_epci et df_geom_reg sont accessibles ici
@st.cache_data
def load_geom():

    df_geom_epci = gpd.read_parquet(DATA_DIR / 'epci_geom_simplified.parquet')
    df_geom_reg = gpd.read_parquet(DATA_DIR / 'regions_geom_simplified.parquet')
    
    return df_geom_epci, df_geom_reg

# ─── ONGLET PRINCIPAL ─────────────────────────────────────────────
tab1, tab6, tab2 = st.tabs([ "🏥 Vue d’ensemble", "Graphique Radar", "📍 Carte des Établissements"
])



# =================================================================
# 🟦 ONGLET 1 — KPI + TYPOLOGIES
# =================================================================
with tab1:
    st.header("Vue d’ensemble des établissements de santé en Occitanie")

    # --- KPI ---
    total_etabs = df_join['numero_finess_etablissement'].nunique()
    nb_types = df['type d etablissements'].nunique()
    nb_deps = df['departement'].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Établissements recensés", f"{total_etabs}")
    col2.metric("Types d’établissements", f"{nb_types}")
    col3.metric("Départements couverts", f"{nb_deps}")
    col4.metric("Nb d'habitants par établissement", f"{df_communes_occitanie['population'].sum()/df['numero_finess_etablissement'].nunique(): .0f}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Établissements recensés en France", f"102553")
    col2.metric("Types d’établissements", f"{nb_types}")
    col3.metric("Départements en France", f"106")
    col4.metric("Nb d'habitants par établissement en France", f"673")

    st.markdown(f"""
                ### 📍 Informations clés
    L'occitanie représente {round(total_etabs/102553*100, 2)} % des établissements de santé en France.
    Avec une population d'environ {df_communes_occitanie['population'].sum():,} habitants, soit 9% de la population française.Cela correspond à environ {round(df_communes_occitanie['population'].sum()/total_etabs):,} personnes par établissement.""")
    
    st.markdown("""### 🎯 Choisissez votre filtre :""")
    # --- CSS pour styliser les boutons Streamlit ---
    st.markdown("""
    <style>
    div.stButton > button {
        background-color: #1f77b4;
        color: white;
        padding: 10px 18px;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        cursor: pointer;
    }
    div.stButton > button:hover {
        background-color: #155a86;
    }
    </style>
    """, unsafe_allow_html=True)


   

    # --- Boutons de filtres rapides ---
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("☀️ Toute l'Occitanie"):
            st.session_state["filtre_epci"] = []

    with col2:
        if st.button("🌇 Métropole de Toulouse"):
            st.session_state["filtre_epci"] = ["Toulouse Métropole"]

    with col3:
        if st.button("🐄 CC Pyrénées Audoises"):
            st.session_state["filtre_epci"] = ["CC Pyrénées Audoises"]


    

    # Récupération du filtre EPCI actif
    filtre_actuel = st.session_state.get("filtre_epci", [])
    
    # Construction du texte à afficher
    if not filtre_actuel:
        titre_filtre = " (Tous EPCI)"
    else:
        titre_filtre = f" ({', '.join(filtre_actuel)})"
    
    # Affichage du titre
    st.subheader("Typologie des établissements" + titre_filtre)

    df_filtre_typo = df_join.copy()
    df_communes_filtrees = df_communes_occitanie.copy()

    if "filtre_epci" in st.session_state and st.session_state["filtre_epci"]:
        df_filtre_typo = df_filtre_typo[
            df_filtre_typo["epci_nom"].isin(st.session_state["filtre_epci"])
        ]
        df_communes_filtrees = df_communes_occitanie[
            df_communes_occitanie["epci_nom"].isin(st.session_state["filtre_epci"])]

    table_typo2 = (
        df_filtre_typo.groupby('type d etablissements')
          .agg(nb_etablissements=('numero_finess_etablissement', 'count'))
          .reset_index()
    )
    # Population totale du périmètre filtré
    population_totale = df_communes_filtrees['population'].sum()



    table_typo2['pourcentage'] = (table_typo2['nb_etablissements'] / df_filtre_typo['numero_finess_etablissement'].nunique() * 100).round(2)
    table_typo2['etabs_pour_100000_habitants'] =  (table_typo2['nb_etablissements'] / population_totale * 100000).round(4)
    table_typo2['population'] =   population_totale 
    table_typo2 = table_typo2.sort_values('nb_etablissements', ascending=False)

    # Ajout d’un indicateur visuel pour les 3 premiers

 # Ajout d’un indicateur visuel pour les 3 premiers
    table_typo2['Classement'] = ""

    classements = ["🥇 TOP 1", "🥈 TOP 2", "🥉 TOP 3"]

    for i, label in enumerate(classements):
        if i < len(table_typo2):
            table_typo2.loc[table_typo2.index[i], "Classement"] = label


    st.dataframe(table_typo2, use_container_width=True, hide_index=True)



    fig_typo2 = px.bar(
        table_typo2,
        x='type d etablissements',
        y='nb_etablissements',
        title="Nombre d'établissements par typologie" + titre_filtre,
        labels={'type d etablissements': 'Typologie', 'nb_etablissements': 'Nombre'},
    )
    st.plotly_chart(fig_typo2, use_container_width=True, key="graph2")


with tab6:
    # ============================
    # RADAR COMPARATIF DYNAMIQUE
    # ============================
    st.markdown(""" ### 📊 Graphique radar ###
                """)
    st.write("Lecture du graphique radar:  Chaque axe représente un type d’établissement. La surface indique la **densité d’établissements rapportée à la population (établissements pour 100 000 habitants)**.")
    import plotly.graph_objects as go

    # --- Fonction utilitaire pour calculer les ratios ---
    def compute_typology(df_etabs, df_communes):
        table = (
            df_etabs.groupby("type d etablissements")
            .agg(nb_etablissements=("numero_finess_etablissement", "count"))
            .reset_index()
        )

        population = df_communes["population"].sum()

        table["etabs_pour_100000_hab"] = (
            table["nb_etablissements"] / population * 100000
        ).round(4)

        return table


    # --- 1) Occitanie entière ---
    table_occ = compute_typology(df_join, df_communes_occitanie)

    # --- 2) Toulouse Métropole (toujours visible) ---
    df_etabs_tm = df_join[df_join["epci_nom"] == "Toulouse Métropole"]
    df_com_tm = df_communes_occitanie[df_communes_occitanie["epci_nom"] == "Toulouse Métropole"]
    table_tm = compute_typology(df_etabs_tm, df_com_tm)


    # --- 3) Sélecteur dynamique d’EPCI ---
    epci_list = sorted(df_communes_occitanie["epci_nom"].dropna().unique())

    selected_epci = st.selectbox(
        "Sélectionner un EPCI pour comparaison :",
        options=["Tous"] + epci_list,
        index=0,
        key="filtre_epci_radar"
    )


    # --- 4) Données de l’EPCI sélectionné ---
    if selected_epci != "Tous":
        df_etabs_epci = df_join[df_join["epci_nom"] == selected_epci]
        df_com_epci = df_communes_occitanie[df_communes_occitanie["epci_nom"] == selected_epci]
        table_epci = compute_typology(df_etabs_epci, df_com_epci)
    else:
        table_epci = None


    # --- 5) Harmonisation des axes (toutes les typologies présentes) ---
    types_all = sorted(table_occ["type d etablissements"].unique())

    def align_table(table, types_all):
        table = table.set_index("type d etablissements").reindex(types_all).fillna(0)
        return table.reset_index()

    table_occ = align_table(table_occ, types_all)
    table_tm = align_table(table_tm, types_all)
    if table_epci is not None:
        table_epci = align_table(table_epci, types_all)


    # --- 6) Radar comparatif ---
    fig = go.Figure()

    # Occitanie
    fig.add_trace(go.Scatterpolar(
        r = table_occ["etabs_pour_100000_hab"],
        theta = table_occ["type d etablissements"],
        fill='toself',
        name='Occitanie',
        line_color="#1f77b4",
        fillcolor="rgba(31, 119, 180, 0.2)"
    ))

    # Toulouse Métropole
    fig.add_trace(go.Scatterpolar(
        r = table_tm["etabs_pour_100000_hab"],
        theta = table_tm["type d etablissements"],
        fill='toself',
        name='Toulouse Métropole',
        line_color="#ff7f0e",
        fillcolor="rgba(255, 127, 14, 0.2)"
    ))

    # EPCI sélectionné (si ≠ Tous)
    if table_epci is not None:
        fig.add_trace(go.Scatterpolar(
            r = table_epci["etabs_pour_100000_hab"],
            theta = table_epci["type d etablissements"],
            fill='toself',
            name=selected_epci,
            line_color="#2ca02c",
            fillcolor="rgba(44, 160, 44, 0.2)"
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True)
        ),
        title=f"Comparatif : Occitanie vs Toulouse Métropole vs {selected_epci}",
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)


# =================================================================
# 🟩 ONGLET 2 — CARTE PAR TYPE D'ÉTABLISSEMENT
# =================================================================
with tab2:
    st.header("Carte interactive des établissements de santé")
# --- Boutons de filtres rapides ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("☀️ Toute l'Occitanie", key="bouton_tout"):
            st.session_state["filtre_epci_carte"] = []
    
    with col2:
        if st.button("🌇 Métropole de Toulouse", key="bouton_toulouse"):
            st.session_state["filtre_epci_carte"] = ["Toulouse Métropole"]
    
    with col3:
        if st.button("🐄 CC Pyrénées Audoises", key="bouton_cc"):
            st.session_state["filtre_epci_carte"] = ["CC Pyrénées Audoises"]

    

    groupes = sorted(df_join['type d etablissements'].dropna().unique())
    departements = sorted(df_join['departement'].dropna().unique())
    epci = sorted(df_join['epci_nom'].dropna().unique())

    option_tous_groupes = "Tous les types"
    option_tous_deps = "Tous les départements"
    option_tous_epci = "Tous les EPCI"

    selection_groupes = st.multiselect(
        "Sélectionner un ou plusieurs types d'établissements :",
        [option_tous_groupes] + groupes,
        default=[option_tous_groupes],
        key="filtre_groupes"
    )

    selection_deps = st.multiselect(
        "Sélectionner un ou plusieurs départements :",
        [option_tous_deps] + departements,
        default=[option_tous_deps],
        key="filtre_departements"
    )

    selection_epci = st.multiselect(
        "Sélectionner un ou plusieurs EPCI :",
        [option_tous_epci] + epci,
        default=[option_tous_epci],
        key="filtre_epci_carte"
    )

    df_filtre = df_join.copy()

    if option_tous_groupes not in selection_groupes:
        df_filtre = df_filtre[df_filtre['type d etablissements'].isin(selection_groupes)]

    if option_tous_deps not in selection_deps:
        df_filtre = df_filtre[df_filtre['departement'].isin(selection_deps)]

    if option_tous_epci not in selection_epci:
            df_filtre = df_filtre[df_filtre['epci_nom'].isin(selection_epci)]

    if not df_filtre.empty:
        center_lat = df_filtre['latitude'].mean()
        center_lon = df_filtre['longitude'].mean()
    else:
        center_lat, center_lon = 46.5, 2.5

    fig = px.scatter_map(
        df_filtre,
        lat="latitude",
        lon="longitude",
        hover_name="raison_sociale",
        hover_data={"type d etablissements": True},
        color="type d etablissements",
        zoom=6,
        height=650
    )

    fig.update_layout(
        map_style="open-street-map",
        map_center={"lat": center_lat, "lon": center_lon},
        margin={"r":0, "t":0, "l":0, "b":0}
    )

    st.plotly_chart(fig, use_container_width=True)








