"""
C2/C3 - Nettoyage et préparation des données FINESS
=====================================================
- Normalisation des colonnes (noms, types)
- Gestion des doublons
- Nettoyage des valeurs nulles et formats
- Filtrage Occitanie (région 76, départements 09,11,12,30,31,32,34,46,48,65,66,81,82)
- Règles d'agrégation pour combiner les 3 sources
- Géoréférencement (Lambert93 → WGS84)
"""

import logging
import math
import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

OCCITANIE_DEPTS = {"09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"}
OCCITANIE_REG = 76

# Mapping 172 catégories → 11 grands types d'établissements
CATEGORY_MAPPING = {
    # Hôpitaux et soins aigus
    "Centre Hospitalier (C.H.)": "Hôpital / Clinique",
    "Centre Hospitalier Régional (C.H.R.)": "Hôpital / Clinique",
    "Centre Hospitalier Universitaire (C.H.U.)": "Hôpital / Clinique",
    "Clinique Psychiatrique": "Psychiatrie",
    "Centre Hospitalier Spécialisé en Psychiatrie": "Psychiatrie",
    "EHPAD": "EHPAD / Personnes âgées",
    "Résidence Autonomie": "EHPAD / Personnes âgées",
    "Maison de Retraite": "EHPAD / Personnes âgées",
    "Institut Médico-Éducatif (I.M.E.)": "Handicap",
    "Maison d'Accueil Spécialisée (M.A.S.)": "Handicap",
    "Foyer d'Accueil Médicalisé pour Adultes Handicapés (F.A.M.)": "Handicap",
    "Centre Médico-Psycho-Pédagogique (C.M.P.P.)": "Pédiatrie / Enfance",
    "Protection Maternelle et Infantile (P.M.I.)": "Pédiatrie / Enfance",
    "Centre de Rééducation et Réadaptation Fonctionnelles": "Rééducation / Réadaptation",
    "Établissement Thermal": "Thermalisme / Cure",
    "Centre de Santé": "Centre de Santé",
    "Laboratoire d'Analyses de Biologie Médicale": "Laboratoire / Pharmacie",
    "Pharmacie": "Laboratoire / Pharmacie",
}

# ---------------------------------------------------------------------------
# Fonctions de nettoyage
# ---------------------------------------------------------------------------

def clean_nofiness(series: pd.Series) -> pd.Series:
    """
    Normalise les numéros FINESS : chaîne de 9 caractères, zéros à gauche.
    Exemples : 10001246 → '010001246', 310001234 → '310001234'
    """
    return series.astype(str).str.zfill(9)


def clean_department(code: str) -> str:
    """Normalise un code département : '9' → '09', '31' → '31'."""
    if pd.isna(code):
        return None
    code = str(code).strip().zfill(2)
    return code[:2]  # Garde uniquement les 2 premiers chiffres


def lambert93_to_wgs84(x: float, y: float):
    """
    Convertit des coordonnées Lambert93 (EPSG:2154) en WGS84 (lat/lon).
    Implémentation pure Python basée sur les paramètres IAG GRS80.
    """
    try:
        if pd.isna(x) or pd.isna(y) or float(x) == 0 or float(y) == 0:
            return None, None
        x, y = float(x), float(y)

        # Paramètres ellipsoïde GRS80
        a = 6378137.0
        e = 0.0818191910428158

        # Paramètres projection Lambert93
        lc = math.radians(3.0)          # Longitude centrale
        phi0 = math.radians(46.5)       # Latitude d'origine
        phi1 = math.radians(44.0)       # Parallèle 1
        phi2 = math.radians(49.0)       # Parallèle 2
        x0 = 700000.0
        y0 = 6600000.0

        def _geo_lat(phi):
            sp = e * math.sin(phi)
            return math.tan(math.pi / 4 + phi / 2) * ((1 - sp) / (1 + sp)) ** (e / 2)

        m1 = math.cos(phi1) / math.sqrt(1 - (e * math.sin(phi1)) ** 2)
        m2 = math.cos(phi2) / math.sqrt(1 - (e * math.sin(phi2)) ** 2)
        t1 = _geo_lat(phi1)
        t2 = _geo_lat(phi2)
        t0 = _geo_lat(phi0)

        n = math.log(m1 / m2) / math.log(t1 / t2)
        F = m1 / (n * t1 ** n)
        r0 = a * F * t0 ** n

        dx, dy = x - x0, y - y0 + r0
        r = math.sqrt(dx ** 2 + dy ** 2) * math.copysign(1, n)
        theta = math.atan(dx / (r0 - (y - y0)))
        lon = math.degrees(theta / n + lc)

        t = (r / (a * F)) ** (1 / n)
        phi = math.pi / 2 - 2 * math.atan(t)
        for _ in range(10):
            sp = e * math.sin(phi)
            phi = math.pi / 2 - 2 * math.atan(t * ((1 - sp) / (1 + sp)) ** (e / 2))

        lat = math.degrees(phi)

        if 41 <= lat <= 52 and -5 <= lon <= 10:
            return round(lat, 6), round(lon, 6)
        return None, None
    except Exception:
        return None, None


def map_category(libcategetab: str) -> str:
    """Mappe une catégorie FINESS vers un grand type d'établissement."""
    if pd.isna(libcategetab):
        return "Non classifié"
    for key, value in CATEGORY_MAPPING.items():
        if key.lower() in libcategetab.lower():
            return value
    return "Autre"


# ---------------------------------------------------------------------------
# Chargement des fichiers sources
# ---------------------------------------------------------------------------

def load_equipements() -> pd.DataFrame:
    """Charge et nettoie le fichier équipements sociaux."""
    logger.info("Chargement : finess_equipements_sociaux.csv")
    path = RAW_DIR / "finess_equipements_sociaux.csv"

    df = pd.read_csv(
        path,
        sep=";",
        dtype=str,  # Tout en string pour éviter la perte de zéros
        encoding="utf-8",
    )

    logger.info(f"  Lignes brutes : {len(df)}")

    # Sélection des colonnes utiles
    cols = ["nofinesset", "nofinessej", "libde", "libta", "libclient", "capinstot"]
    df = df[[c for c in cols if c in df.columns]].copy()

    # Nettoyage
    df["nofinesset"] = clean_nofiness(df["nofinesset"])
    df["nofinessej"] = clean_nofiness(df["nofinessej"])
    df["capinstot"] = pd.to_numeric(df["capinstot"], errors="coerce")

    # Renommage des colonnes
    df = df.rename(columns={
        "libde": "type_equipement",
        "libta": "mode_accueil",
        "libclient": "public_cible",
        "capinstot": "capacite_installee",
    })

    # Suppression des doublons exacts
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"  Doublons supprimés : {before - len(df)}")
    logger.info(f"  Lignes nettoyées : {len(df)}")

    return df


def load_activites() -> pd.DataFrame:
    """Charge et nettoie le fichier activités de soins."""
    logger.info("Chargement : finess_activites_soin.csv")
    path = RAW_DIR / "finess_activites_soin.csv"

    df = pd.read_csv(path, sep=";", dtype=str, encoding="utf-8")
    logger.info(f"  Lignes brutes : {len(df)}")

    cols = ["nofinesset", "nofinessej", "libactivite", "libmodalite", "libforme", "datemeo", "datefin"]
    df = df[[c for c in cols if c in df.columns]].copy()

    df["nofinesset"] = clean_nofiness(df["nofinesset"])
    df["nofinessej"] = clean_nofiness(df["nofinessej"])

    # Nettoyage des dates
    for col in ["datemeo", "datefin"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    # Renommage
    df = df.rename(columns={
        "libactivite": "activite",
        "libmodalite": "modalite",
        "libforme": "forme",
    })

    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"  Doublons supprimés : {before - len(df)}")
    logger.info(f"  Lignes nettoyées : {len(df)}")

    return df


def load_communes() -> pd.DataFrame:
    """Charge le référentiel communes INSEE 2025."""
    logger.info("Chargement : v_commune_2025.csv")
    path = RAW_DIR / "v_commune_2025.csv"

    df = pd.read_csv(path, dtype=str, encoding="utf-8")

    df = df[["COM", "DEP", "REG", "LIBELLE"]].copy()
    df = df.rename(columns={"COM": "code_commune", "DEP": "departement", "REG": "region", "LIBELLE": "nom_commune"})
    df["region"] = pd.to_numeric(df["region"], errors="coerce")

    logger.info(f"  Communes chargées : {len(df)}")
    return df


# ---------------------------------------------------------------------------
# Construction de la table centrale établissements
# ---------------------------------------------------------------------------

def build_etablissements(df_eq: pd.DataFrame, df_ac: pd.DataFrame, df_communes: pd.DataFrame) -> pd.DataFrame:
    """
    Règles d'agrégation pour construire la table établissements Occitanie.

    Logique :
    1. Base = équipements sociaux (contient nofinesset + infos établissement)
    2. Enrichissement avec activités de soins (jointure 1-N sur nofinesset)
    3. Jointure avec communes pour enrichissement géographique
    4. Filtrage sur Occitanie via code département
    5. Géoréférencement si coordonnées disponibles
    """
    logger.info("\nConstruction de la table établissements...")

    # Extraction des infos uniques par établissement depuis équipements
    etab_cols = ["nofinesset", "nofinessej"]
    df_etab = df_eq[etab_cols].drop_duplicates(subset=["nofinesset"]).copy()

    # Agrégation des équipements par établissement (capacité totale, types)
    agg_eq = df_eq.groupby("nofinesset").agg(
        nb_equipements=("type_equipement", "count"),
        capacite_totale=("capacite_installee", "sum"),
        types_equipements=("type_equipement", lambda x: " | ".join(x.dropna().unique())),
        modes_accueil=("mode_accueil", lambda x: " | ".join(x.dropna().unique())),
        public_cible=("public_cible", lambda x: " | ".join(x.dropna().unique())),
    ).reset_index()

    df_etab = df_etab.merge(agg_eq, on="nofinesset", how="left")

    # Agrégation des activités de soins par établissement
    agg_ac = df_ac.groupby("nofinesset").agg(
        nb_activites=("activite", "count"),
        activites=("activite", lambda x: " | ".join(x.dropna().unique())),
        modalites=("modalite", lambda x: " | ".join(x.dropna().unique())),
    ).reset_index()

    df_etab = df_etab.merge(agg_ac, on="nofinesset", how="left")

    # Extraction code département depuis nofinesset (2 premiers chiffres)
    df_etab["departement"] = df_etab["nofinesset"].str[:2]
    df_etab["departement"] = df_etab["departement"].apply(clean_department)

    # Filtrage Occitanie
    before = len(df_etab)
    df_occitanie = df_etab[df_etab["departement"].isin(OCCITANIE_DEPTS)].copy()
    logger.info(f"  Filtre Occitanie : {before} → {len(df_occitanie)} établissements")

    # Jointure avec communes pour nom du département
    dept_names = {
        "09": "Ariège", "11": "Aude", "12": "Aveyron", "30": "Gard",
        "31": "Haute-Garonne", "32": "Gers", "34": "Hérault", "46": "Lot",
        "48": "Lozère", "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales",
        "81": "Tarn", "82": "Tarn-et-Garonne"
    }
    df_occitanie["nom_departement"] = df_occitanie["departement"].map(dept_names)
    df_occitanie["region"] = "Occitanie"

    # Indicateurs booléens
    df_occitanie["a_activite_soins"] = df_occitanie["nb_activites"].notna() & (df_occitanie["nb_activites"] > 0)
    df_occitanie["a_equipement_social"] = df_occitanie["nb_equipements"].notna() & (df_occitanie["nb_equipements"] > 0)

    # Remplissage des valeurs nulles numériques
    for col in ["nb_equipements", "capacite_totale", "nb_activites"]:
        df_occitanie[col] = df_occitanie[col].fillna(0).astype(int)

    logger.info(f"  Table finale : {len(df_occitanie)} établissements")
    return df_occitanie


# ---------------------------------------------------------------------------
# Rapport de qualité
# ---------------------------------------------------------------------------

def quality_report(df: pd.DataFrame) -> dict:
    """Génère un rapport sur la qualité du jeu de données."""
    report = {
        "total_etablissements": len(df),
        "colonnes": list(df.columns),
        "valeurs_nulles": df.isnull().sum().to_dict(),
        "departements": df["departement"].value_counts().to_dict(),
        "avec_activite_soins": int(df["a_activite_soins"].sum()),
        "avec_equipement_social": int(df["a_equipement_social"].sum()),
        "capacite_totale_region": int(df["capacite_totale"].sum()),
        "taux_completude_pct": round(
            (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100, 1
        ),
    }
    return report


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def prepare() -> pd.DataFrame:
    """Pipeline complet de préparation des données."""
    logger.info("=" * 60)
    logger.info("DÉMARRAGE DU NETTOYAGE ET PRÉPARATION")
    logger.info("=" * 60)

    # Chargement
    df_eq = load_equipements()
    df_ac = load_activites()
    df_communes = load_communes()

    # Construction table principale
    df_final = build_etablissements(df_eq, df_ac, df_communes)

    # Rapport qualité
    report = quality_report(df_final)
    logger.info("\nRAPPORT QUALITÉ")
    logger.info(f"  Établissements Occitanie : {report['total_etablissements']}")
    logger.info(f"  Avec activités soins     : {report['avec_activite_soins']}")
    logger.info(f"  Avec équipements sociaux : {report['avec_equipement_social']}")
    logger.info(f"  Capacité totale région   : {report['capacite_totale_region']:,} places")
    logger.info(f"  Taux de complétude       : {report['taux_completude_pct']}%")

    # Export
    out_path = PROCESSED_DIR / "etablissements_occitanie.csv"
    df_final.to_csv(out_path, index=False, encoding="utf-8")
    logger.info(f"\n✓ Fichier exporté : {out_path}")

    # Export aussi des tables détail pour l'API
    df_eq_occ = df_eq[df_eq["nofinesset"].str[:2].isin(OCCITANIE_DEPTS)]
    df_eq_occ.to_csv(PROCESSED_DIR / "equipements_occitanie.csv", index=False, encoding="utf-8")

    df_ac_occ = df_ac[df_ac["nofinesset"].str[:2].isin(OCCITANIE_DEPTS)]
    df_ac_occ.to_csv(PROCESSED_DIR / "activites_occitanie.csv", index=False, encoding="utf-8")

    logger.info("=" * 60)
    logger.info("PRÉPARATION TERMINÉE")
    logger.info("=" * 60)

    return df_final


if __name__ == "__main__":
    prepare()
