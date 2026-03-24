# 🏥 Santé & Territoire — Analyse des établissements de santé (FINESS)
Projet démonstratif pour la certification RNCP37827BC01 — Data Analyst / Data Engineer
Ce projet met en œuvre l’ensemble des compétences attendues dans le cadre de la certification RNCP37827BC01, à travers l’analyse territoriale des établissements de santé en France à partir des données ouvertes FINESS. Il illustre ma capacité à construire un pipeline complet : collecte, transformation, modélisation, visualisation et restitution interactive.

## 🎯 Finalité du projet
- Produire une analyse territoriale fiable et reproductible des établissements sanitaires.
- Démontrer mes compétences en Data Engineering, Data Analysis, visualisation, qualité des données et communication.
- Restituer les résultats via un dashboard Streamlit destiné à des acteurs publics (ARS, collectivités, décideurs).

## 🧩 Compétences RNCP démontrées
# 📥 1. Collecte et préparation des données
- Identification et sélection des sources ouvertes officielles (FINESS – data.gouv.fr).
- Téléchargement, versioning et documentation des fichiers bruts.
- Mise en place d’un pipeline d’ingestion structuré (scripts ETL).
- Gestion des formats hétérogènes (CSV, txt).
- Donnés stockées sur Google BigQuery
# 🧹 2. Nettoyage, contrôle qualité et transformation
- Normalisation des colonnes (types, formats) en SQL dans Big Query. 
- Détection et traitement des valeurs manquantes, doublons, incohérences.
- Enrichissement des données avec des référentiels territoriaux (départements, régions).
- Structuration des données dans un format exploitable pour l’analyse et la visualisation.
# 📊 3. Analyse statistique et territoriale
- Calcul d’indicateurs clés :
- Nombre d’établissements par région / département
- Répartition par typologie
- Densité territoriale
- Mise en évidence de disparités régionales et dynamiques territoriales.
- Construction de tableaux filtrables et de KPI synthétiques.
# 🗺️ 4. Visualisation et communication des résultats
- Création de cartes choroplèthes (répartition géographique).
- Graphiques interactifs (Plotly) : distributions, comparaisons, tendances.
- Tableaux dynamiques pour l’exploration fine.
- Conception d’un dashboard Streamlit clair, ergonomique et orienté décideurs.
# 🧱 5. Développement d’un pipeline reproductible
- Organisation modulaire du code (ETL, analyse, visualisation, app).
- Scripts réutilisables et documentés.
- Gestion des dépendances via requirements.txt.
- Structuration du projet selon les bonnes pratiques Data Engineering.
# 🗂️ 6. Documentation et présentation professionnelle
- Rédaction d’un README complet et orienté compétences.
- Explication des choix techniques et méthodologiques.
- Production de visuels et d’une interface adaptée à un public non technique.
- Préparation à la soutenance RNCP (clarté, justification, pédagogie).

# 📦 Données utilisées
Les données proviennent des fichiers FINESS publiés par le Ministère de la Santé sur data.gouv.fr.
Elles incluent : identifiants, typologies, statuts, adresses, géolocalisation, rattachements territoriaux.


---

## 🛠️ Installation

### Prérequis

- Python 3.11.8
- pyenv (recommandé) ou venv

### Setup avec pyenv (recommandé)

```bash
# Cloner le projet
git clone https://github.com/stluria/sante-territoire-rncp.git
cd sante-territoire-rncp

# Créer l'environnement virtuel
pyenv virtualenv 3.11.8 sante-territoire-rncp
# L'activation sera automatique grâce au .python-version

# Installer les dépendances
pip install -r requirements.txt

# Vérifier que tout fonctionne
python -c "import pandas, geopandas; print('✅ Prêt !')"
```

### Setup avec venv standard

```bash
# Cloner le projet
git clone https://github.com/stluria/sante-territoire-rncp.git
cd sante-territoire-rncp

# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
source venv/bin/activate  # Mac/Linux
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

---

## 📁 Structure du projet

```
├── data/
│   ├── raw/          # Données brutes FINESS
│   ├── processed/    # Données nettoyées et enrichies
├── src/
│   ├── etl/          # Scripts d'extraction, nettoyage, transformation
│   ├── analysis/     # Analyses statistiques et territoriales
│   ├── viz/          # Graphiques, cartes, KPI
│   └── app/          # Application Streamlit
├── dashboard/         # Captures ou version déployée
├── README.md
└── requirements.txt
```

---

## 📊 Données

### Sources de données utilisées

#### Données géographiques
- 


#### Données de santé
- **FINESS** : Liste des établissements du domaine sanitaire et social. Une table pour les différentes offres de soins, une pour le matériel. 


### Emplacement des données

- Les données brutes sont stockées dans `data/raw/`
- Les données géographiques dans `data/geo/`
- Les données transformées dans `data/processed/`

**Note** : Les fichiers de données ne sont pas versionnés (voir `.gitignore`)

---

## 🚀 Usage

### Exploration des données

```bash
# Lancer Jupyter Notebook
jupyter notebook notebooks/01_exploration.ipynb
```

### Dashboard interactif (si implémenté)

```bash
# Lancer le dashboard Streamlit
streamlit run app.py
```

### Analyses

Les scripts d'analyse se trouvent dans le dossier `src/` et peuvent être exécutés individuellement ou importés dans les notebooks.

---



---





## 📚 Ressources

### Contexte du projet
- [Défi Open Data University - Santé et territoires](https://defis.data.gouv.fr/defis/)
- [Fondation Roche - Observatoire de l'accès au numérique en santé](https://www.fondationroche.org/)

### Documentation technique
- [GeoPandas Documentation](https://geopandas.org/)
- [Folium Documentation](https://python-visualization.github.io/folium/)
- [Streamlit Documentation](https://docs.streamlit.io/)

### Données ouvertes
- [data.gouv.fr - Santé](https://www.data.gouv.fr/fr/pages/donnees-sante/)
- [INSEE - Données démographiques](https://www.insee.fr/)

---

## 📝 Licence

Ce projet est réalisé dans le cadre d'un projet pédagogique.

---

## 🤝 Contribution

Pour contribuer au projet :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit les changements (`git commit -m 'Ajout nouvelle analyse'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

---
## 🚀 Dashboard Streamlit
Le dashboard permet :
- Une exploration interactive des établissements.
- Des filtres par région, département, typologie, statut.
- Une carte choroplèthe dynamique.
- Des KPI synthétiques pour les décideurs.
(Lien à ajouter si déployé)

## 🔭 Perspectives d’évolution
- Intégration de données INSEE pour croiser démographie et offre de soins.
- Analyse temporelle (ouvertures / fermetures).
- Calcul d’indicateurs d’accessibilité (isochrones).
- Automatisation complète du pipeline (CI/CD).

## 📧 Contact

Pour toute question sur le projet, contactez-moi sur stluria@gmail.com 
