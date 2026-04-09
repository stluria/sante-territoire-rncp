import streamlit as st
# ---------------------------------------------------------
# CONFIGURATION DE LA PAGE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Conclusion",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.title("📊 Conclusion : Comment aider les acteurs locaux à réaliser un diagnostic de santé publique relatifs aux Etablissements sur leur territoire en Occitanie?")
st.subheader("Analyse, automatisation et visualisation de données")

st.markdown(
    """
Bienvenue sur le tableau de bord interactif réalisé dans le cadre du projet de fin d'études.  
Ce site présente l’ensemble des analyses, visualisations et outils développés autour du jeu de données sélectionné.

---
"""
)

# ---------------------------------------------------------
# OBJECTIFS DU PROJET
# ---------------------------------------------------------
st.header("🎯 Conclusion relatives aux données ")

st.markdown(
    """
Les données exploitées depuis les fichiers Finess permettent de mettre en avant les établissements, les prestations de soins disponibles et les prestations sociales et médico sociales. 
En revanche, il n'y a pas de données liées au capacité d'accueil de des établissements et des prestations de soins. 
L'idéal aurait été de pouvoir avoir des données afin d'optimiser l'analyse. 

Néanmoins, il ressort les éléments suivants  : 

"""
)

# ---------------------------------------------------------
# STRUCTURE DU TABLEAU DE BORD
# ---------------------------------------------------------
st.header("🗂️ Navigation dans l'application")

st.markdown(
    """
L'application est organisée en plusieurs sections accessibles via le menu latéral :

- **app** : Présentation générale du projet.  
- **🗺️ Carte globale** : Carte générale.
- **🏢 Etablissements** : Données relatives aux établissements de santé en 2026.
- **📌 KPI** : KPI.
- **🩺 Soins** : Données relatives aux prestations de soins de santé en 2026.
- **👨‍👩‍👧‍👦 Social** : Données relatives aux prestations sociales et médico-sociales en 2026.
- **📖 Lexique** : Lexique utilisé  

"""
)

# ---------------------------------------------------------
# METHODOLOGIE
# ---------------------------------------------------------
st.header("🧭 Méthodologie")

st.markdown(
    """
La démarche suivie repose sur les étapes classiques d’un projet data :

1. **Compréhension du besoin métier**  
2. **Collecte et exploration des données**  
3. **Nettoyage et préparation (ETL)**  
4. **Analyses statistiques et visualisations**   
5. **Déploiement Streamlit**