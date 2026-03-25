import streamlit as st
import plotly.express as px
import pandas as pd
import geopandas as gpd
import folium
#from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from pathlib import Path
from streamlit_folium import st_folium

# On essaie d'utiliser __file__, sinon on prend le dossier actuel
try:
    BASE_DIR = Path(__file__).resolve().parent
except NameError:
    BASE_DIR = Path.cwd()

ROOT = BASE_DIR.parent
DATA_DIR = ROOT / "data"


# --- CONFIGURATION ---
st.set_page_config(page_title="Carte de l'Occitanie", layout="wide")

# --- CHARGEMENT DES DONNÉES ---
# Assurez-vous que df_geom_epci et df_geom_reg sont accessibles ici
@st.cache_data
def load_geom():

    df_geom_epci = gpd.read_parquet(DATA_DIR / 'epci_geom_simplified.parquet')
    df_geom_reg = gpd.read_parquet(DATA_DIR / 'regions_geom_simplified.parquet')
    
    return df_geom_epci, df_geom_reg




st.header("Contexte Géographique : Relief et Littoral")
    
df_geom_epci, df_geom_reg = load_geom()
    
# 1. Récupération de la ligne de la région Occitanie
region_occ = df_geom_reg[df_geom_reg['code_siren'] == '200053791']

if not region_occ.empty:
    # Utilisation directe des colonnes lon et lat du fichier
    occ_center = [region_occ['lat'].iloc[0], region_occ['lon'].iloc[0]]
    
    # Initialisation de la carte avec le centre du fichier
    m = folium.Map(
        location=occ_center, 
        zoom_start=7, 
        tiles="OpenStreetMap",
        control_scale=True
    )
    # 2. Ajout des polygones (GeoJson)
    # Contour Région
    folium.GeoJson(
        region_occ,
        style_function=lambda x: {'fillColor': 'none', 'color': '#333333', 'weight': 3}
    ).add_to(m)
    # EPCI Cibles
    cibles_info = {
        '243100518': {'nom': 'Toulouse Métropole', 'color': '#1f77b4'},
        '200043776': {'nom': 'CC des Pyrénées Audoises', 'color': '#ff7f0e'}
    }
    
    # --- Dans votre boucle d'affichage des EPCI cibles ---
    for siren, info in cibles_info.items():
        subset = df_geom_epci[df_geom_epci['code_siren'] == siren]
        
        if not subset.empty:
            # 1. Dessiner le polygone
            folium.GeoJson(
                subset,
                style_function=lambda x, color=info['color']: {
                    'fillColor': color, 'color': 'black', 'weight': 2, 'fillOpacity': 0.6
                },
                tooltip=info['nom']
            ).add_to(m)
    
            # 2. Ajouter l'étiquette de texte fixe (Uniquement pour l'Aude ou les deux)
            # On récupère lon/lat directement de votre fichier
            folium.map.Marker(
                location=[subset['lat'].iloc[0], subset['lon'].iloc[0]],
                icon=folium.DivIcon(
                html=f"""<div style="
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    color: #333;
                    font-weight: bold;
                    font-size: 11px;
                    background-color: rgba(255, 255, 255, 0.8);
                    border: 1px solid #999;
                    border-radius: 3px;
                    padding: 2px 5px;
                    white-space: nowrap;
                    text-align: center;
                    ">
                        {info['nom']}
                        </div>""",
                    icon_anchor=(50, 0) # Ajuste le décalage pour centrer le texte
                )
            ).add_to(m)
    
    # 3. Ajustement automatique aux limites (pour ne pas voir toute la France)
    # On définit les coins Sud-Ouest et Nord-Est à partir de la géométrie
    bounds = region_occ.geometry.total_bounds # [minx, miny, maxx, maxy]
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    # 4. Affichage Streamlit (syntaxe 2026)
    st_folium(m, width='stretch', height=600, returned_objects=[])
else:
    st.warning("Données de la région Occitanie non trouvées.")

st.caption("""
    La comparaison de Toulouse Métropole avec la CC des Pyrénées Audoises incarne les contrastes structurels de la région Occitanie. 
    Elle met en exergue le 'grand écart' territorial entre un pôle urbain hyper-connecté, porté par une dynamique démographique soutenue, 
    et un espace rural de faible densité dont l'accès aux infrastructures de santé est conditionné par l'enclavement géographique et les contraintes du relief pyrénéen.
""")