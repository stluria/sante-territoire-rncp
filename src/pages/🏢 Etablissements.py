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
st.set_page_config(page_title="Offres de soins - Occitanie", layout="wide")

# --- CHARGEMENT DES DONNÉES ---
# Assurez-vous que df_geom_epci et df_geom_reg sont accessibles ici
@st.cache_data
def load_geom():

    df_geom_epci = gpd.read_parquet(DATA_DIR / 'epci_geom_simplified.parquet')
    df_geom_reg = gpd.read_parquet(DATA_DIR / 'regions_geom_simplified.parquet')
    
    return df_geom_epci, df_geom_reg

# ─── ONGLET PRINCIPAL ─────────────────────────────────────────────
tab1, tab6, tab2, tab3, tab4,  tab5 = st.tabs([ "🏥 Vue d’ensemble", "Graphique Radar", "📍 Carte des Établissements", "🩺 Soins",  "🚑 Distances aux urgences", "🏠 Social et médico-social"
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


    st.write("Je suis en pleine largeur")

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
               Lecture du graphique radar:  Chaque axe représente un type d’établissement. La surface indique la densité d’établissements rapportée à la population (établissements pour 100 000 habitants). """)

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







# =================================================================
# 🟧 ONGLET - PRESTATIONS SOCIALES
# =================================================================
# 2. INDICATEURS CLÉS
# ───────────────────────────────────────────────
with tab5:
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
