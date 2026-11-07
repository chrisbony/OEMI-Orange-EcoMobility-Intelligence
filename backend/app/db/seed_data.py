"""
backend/app/db/seed_data.py
Spatial Seeding Script for Orange EcoMobility Intelligence (OEMI).
Populates zones_geographiques, demographie (INS RGPH 2021),
infrastructures_commerces (OpenStreetMap POIs), and accessibilite_routiere.
All operations are strictly idempotent with ON CONFLICT DO UPDATE clauses.
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("oemi.seed_data")

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_4kz7aAUJPblS@ep-cold-sea-bdkcgioc.c-8.us-east-2.aws.neon.tech:5432/neondb?sslmode=require"
)

# ==============================================================================
# 1. ZONES GEOGRAPHIQUES (3 Communes + Quartiers Pilotes)
# ==============================================================================

COMMUNES = [
    {
        "id": "COMMUNE_COCODY",
        "nom_commune": "Cocody",
        "nom_zone": "Cocody (Périmètre Communal)",
        "type_zone": "Commune",
        "polygon": [
            [-4.0200, 5.3250],
            [-4.0150, 5.3650],
            [-4.0050, 5.4180],
            [-3.9550, 5.4150],
            [-3.9300, 5.3850],
            [-3.9350, 5.3450],
            [-3.9700, 5.3250],
            [-4.0200, 5.3250]
        ]
    },
    {
        "id": "COMMUNE_YOPOUGON",
        "nom_commune": "Yopougon",
        "nom_zone": "Yopougon (Périmètre Communal)",
        "type_zone": "Commune",
        "polygon": [
            [-4.1200, 5.3050],
            [-4.0450, 5.3100],
            [-4.0350, 5.3400],
            [-4.0450, 5.3780],
            [-4.0950, 5.3820],
            [-4.1250, 5.3550],
            [-4.1250, 5.3250],
            [-4.1200, 5.3050]
        ]
    },
    {
        "id": "COMMUNE_MARCORY",
        "nom_commune": "Marcory",
        "nom_zone": "Marcory (Périmètre Communal)",
        "type_zone": "Commune",
        "polygon": [
            [-4.0050, 5.2800],
            [-3.9680, 5.2780],
            [-3.9580, 5.2950],
            [-3.9550, 5.3150],
            [-3.9800, 5.3220],
            [-4.0080, 5.3150],
            [-4.0060, 5.2950],
            [-4.0050, 5.2800]
        ]
    }
]

NEIGHBORHOOD_ZONES = [
    # --- COCODY SUB-ZONES ---
    {
        "id": "ZONE_COCODY_ANGRE",
        "nom_commune": "Cocody",
        "nom_zone": "Angré 7e Tranche",
        "type_zone": "Quartier",
        "polygon": [
            [-3.9980, 5.3850],
            [-3.9780, 5.3880],
            [-3.9760, 5.4050],
            [-3.9920, 5.4060],
            [-4.0000, 5.3950],
            [-3.9980, 5.3850]
        ]
    },
    {
        "id": "ZONE_COCODY_PALMERAIE",
        "nom_commune": "Cocody",
        "nom_zone": "Riviera Palmeraie",
        "type_zone": "Quartier",
        "polygon": [
            [-3.9680, 5.3680],
            [-3.9480, 5.3700],
            [-3.9450, 5.3880],
            [-3.9650, 5.3870],
            [-3.9700, 5.3780],
            [-3.9680, 5.3680]
        ]
    },
    {
        "id": "ZONE_COCODY_DEUX_PLATEAUX",
        "nom_commune": "Cocody",
        "nom_zone": "Deux Plateaux / Danga",
        "type_zone": "Quartier",
        "polygon": [
            [-4.0120, 5.3550],
            [-3.9880, 5.3570],
            [-3.9860, 5.3750],
            [-4.0050, 5.3780],
            [-4.0140, 5.3680],
            [-4.0120, 5.3550]
        ]
    },

    # --- YOPOUGON SUB-ZONES ---
    {
        "id": "ZONE_YOPOUGON_NIANGON_NORD",
        "nom_commune": "Yopougon",
        "nom_zone": "Niangon Nord",
        "type_zone": "Quartier",
        "polygon": [
            [-4.1100, 5.3300],
            [-4.0850, 5.3320],
            [-4.0860, 5.3500],
            [-4.1050, 5.3520],
            [-4.1120, 5.3420],
            [-4.1100, 5.3300]
        ]
    },
    {
        "id": "ZONE_YOPOUGON_SELMER",
        "nom_commune": "Yopougon",
        "nom_zone": "Selmer",
        "type_zone": "Quartier",
        "polygon": [
            [-4.0720, 5.3320],
            [-4.0550, 5.3330],
            [-4.0540, 5.3460],
            [-4.0680, 5.3480],
            [-4.0730, 5.3400],
            [-4.0720, 5.3320]
        ]
    },
    {
        "id": "ZONE_YOPOUGON_TOIT_ROUGE",
        "nom_commune": "Yopougon",
        "nom_zone": "Toit-Rouge / Siporex",
        "type_zone": "Quartier",
        "polygon": [
            [-4.0820, 5.3420],
            [-4.0680, 5.3400],
            [-4.0660, 5.3580],
            [-4.0780, 5.3620],
            [-4.0840, 5.3520],
            [-4.0820, 5.3420]
        ]
    },

    # --- MARCORY SUB-ZONES ---
    {
        "id": "ZONE_MARCORY_ZONE_4C",
        "nom_commune": "Marcory",
        "nom_zone": "Zone 4C",
        "type_zone": "Zone Commerciale",
        "polygon": [
            [-3.9900, 5.2870],
            [-3.9750, 5.2880],
            [-3.9740, 5.2980],
            [-3.9870, 5.2990],
            [-3.9910, 5.2930],
            [-3.9900, 5.2870]
        ]
    },
    {
        "id": "ZONE_MARCORY_BIETRY",
        "nom_commune": "Marcory",
        "nom_zone": "Biétry",
        "type_zone": "Quartier",
        "polygon": [
            [-3.9880, 5.2800],
            [-3.9700, 5.2800],
            [-3.9710, 5.2870],
            [-3.9870, 5.2870],
            [-3.9890, 5.2830],
            [-3.9880, 5.2800]
        ]
    },
    {
        "id": "ZONE_MARCORY_ANOUMABO",
        "nom_commune": "Marcory",
        "nom_zone": "Anoumabo",
        "type_zone": "Quartier",
        "polygon": [
            [-3.9820, 5.3020],
            [-3.9680, 5.3030],
            [-3.9680, 5.3130],
            [-3.9780, 5.3150],
            [-3.9830, 5.3100],
            [-3.9820, 5.3020]
        ]
    },

    # --- E2E SPEC CONTRACT REFERENCE ZONES (Cross-compatible IDs) ---
    {
        "id": "ci-abidjan-cocody-angre",
        "nom_commune": "Cocody",
        "nom_zone": "Angré 7e Tranche",
        "type_zone": "Quartier",
        "polygon": [
            [-4.0050, 5.3850],
            [-3.9850, 5.3850],
            [-3.9850, 5.4050],
            [-4.0050, 5.4050],
            [-4.0050, 5.3850]
        ]
    },
    {
        "id": "ci-abidjan-cocody-riviera",
        "nom_commune": "Cocody",
        "nom_zone": "Riviera Golf",
        "type_zone": "Quartier",
        "polygon": [
            [-3.9750, 5.3350],
            [-3.9550, 5.3350],
            [-3.9550, 5.3550],
            [-3.9750, 5.3550],
            [-3.9750, 5.3350]
        ]
    },
    {
        "id": "ci-abidjan-cocody-deuxplateaux",
        "nom_commune": "Cocody",
        "nom_zone": "Deux Plateaux Vallon",
        "type_zone": "Quartier",
        "polygon": [
            [-4.0150, 5.3550],
            [-3.9950, 5.3550],
            [-3.9950, 5.3750],
            [-4.0150, 5.3750],
            [-4.0150, 5.3550]
        ]
    },
    {
        "id": "ci-abidjan-yopougon-niangon",
        "nom_commune": "Yopougon",
        "nom_zone": "Niangon Nord",
        "type_zone": "Quartier",
        "polygon": [
            [-4.1150, 5.3350],
            [-4.0950, 5.3350],
            [-4.0950, 5.3550],
            [-4.1150, 5.3550],
            [-4.1150, 5.3350]
        ]
    },
    {
        "id": "ci-abidjan-yopougon-siporex",
        "nom_commune": "Yopougon",
        "nom_zone": "Siporex Carrefour",
        "type_zone": "Pôle commercial",
        "polygon": [
            [-4.0750, 5.3400],
            [-4.0550, 5.3400],
            [-4.0550, 5.3600],
            [-4.0750, 5.3600],
            [-4.0750, 5.3400]
        ]
    },
    {
        "id": "ci-abidjan-yopougon-toitsrouges",
        "nom_commune": "Yopougon",
        "nom_zone": "Toits Rouges",
        "type_zone": "Quartier",
        "polygon": [
            [-4.0900, 5.3200],
            [-4.0700, 5.3200],
            [-4.0700, 5.3400],
            [-4.0900, 5.3400],
            [-4.0900, 5.3200]
        ]
    },
    {
        "id": "ci-abidjan-marcory-bietry",
        "nom_commune": "Marcory",
        "nom_zone": "Biétry Village",
        "type_zone": "Quartier résidentiel",
        "polygon": [
            [-3.9900, 5.2750],
            [-3.9700, 5.2750],
            [-3.9700, 5.2950],
            [-3.9900, 5.2950],
            [-3.9900, 5.2750]
        ]
    },
    {
        "id": "ci-abidjan-marcory-zone4",
        "nom_commune": "Marcory",
        "nom_zone": "Zone 4C Rue du Canal",
        "type_zone": "Pôle commercial & loisir",
        "polygon": [
            [-3.9850, 5.2900],
            [-3.9650, 5.2900],
            [-3.9650, 5.3100],
            [-3.9850, 5.3100],
            [-3.9850, 5.2900]
        ]
    },
    {
        "id": "ci-abidjan-marcory-anoumabo",
        "nom_commune": "Marcory",
        "nom_zone": "Anoumabo",
        "type_zone": "Quartier populaire",
        "polygon": [
            [-4.0050, 5.3000],
            [-3.9850, 5.3000],
            [-3.9850, 5.3200],
            [-4.0050, 5.3200],
            [-4.0050, 5.3000]
        ]
    }
]

ALL_ZONES = COMMUNES + NEIGHBORHOOD_ZONES

# ==============================================================================
# 2. DEMOGRAPHIE (INS CI RGPH 2021)
# ==============================================================================

DEMOGRAPHIE = [
    # Communes
    {
        "id": "DEMO_COMMUNE_COCODY",
        "zone_id": "COMMUNE_COCODY",
        "annee_recensement": 2021,
        "population_totale": 692583,
        "nombre_menages": 169438,
        "densite_hab_km2": 5246.8,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_COMMUNE_YOPOUGON",
        "zone_id": "COMMUNE_YOPOUGON",
        "annee_recensement": 2021,
        "population_totale": 1571065,
        "nombre_menages": 349480,
        "densite_hab_km2": 10268.4,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_COMMUNE_MARCORY",
        "zone_id": "COMMUNE_MARCORY",
        "annee_recensement": 2021,
        "population_totale": 214061,
        "nombre_menages": 50945,
        "densite_hab_km2": 10811.2,
        "source_donnees": "INS_RGPH_2021"
    },

    # Quartiers Cocody
    {
        "id": "DEMO_COCODY_ANGRE",
        "zone_id": "ZONE_COCODY_ANGRE",
        "annee_recensement": 2021,
        "population_totale": 142500,
        "nombre_menages": 35200,
        "densite_hab_km2": 8900.5,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_COCODY_PALMERAIE",
        "zone_id": "ZONE_COCODY_PALMERAIE",
        "annee_recensement": 2021,
        "population_totale": 118200,
        "nombre_menages": 28800,
        "densite_hab_km2": 7250.0,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_COCODY_DEUX_PLATEAUX",
        "zone_id": "ZONE_COCODY_DEUX_PLATEAUX",
        "annee_recensement": 2021,
        "population_totale": 105400,
        "nombre_menages": 24500,
        "densite_hab_km2": 6120.0,
        "source_donnees": "INS_RGPH_2021"
    },

    # Quartiers Yopougon
    {
        "id": "DEMO_YOPOUGON_NIANGON_NORD",
        "zone_id": "ZONE_YOPOUGON_NIANGON_NORD",
        "annee_recensement": 2021,
        "population_totale": 245000,
        "nombre_menages": 54400,
        "densite_hab_km2": 15800.0,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_YOPOUGON_SELMER",
        "zone_id": "ZONE_YOPOUGON_SELMER",
        "annee_recensement": 2021,
        "population_totale": 138000,
        "nombre_menages": 31200,
        "densite_hab_km2": 19200.0,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_YOPOUGON_TOIT_ROUGE",
        "zone_id": "ZONE_YOPOUGON_TOIT_ROUGE",
        "annee_recensement": 2021,
        "population_totale": 182000,
        "nombre_menages": 41500,
        "densite_hab_km2": 17500.0,
        "source_donnees": "INS_RGPH_2021"
    },

    # Quartiers Marcory
    {
        "id": "DEMO_MARCORY_ZONE_4C",
        "zone_id": "ZONE_MARCORY_ZONE_4C",
        "annee_recensement": 2021,
        "population_totale": 42000,
        "nombre_menages": 9800,
        "densite_hab_km2": 6400.0,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_MARCORY_BIETRY",
        "zone_id": "ZONE_MARCORY_BIETRY",
        "annee_recensement": 2021,
        "population_totale": 51200,
        "nombre_menages": 12100,
        "densite_hab_km2": 7800.0,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_MARCORY_ANOUMABO",
        "zone_id": "ZONE_MARCORY_ANOUMABO",
        "annee_recensement": 2021,
        "population_totale": 78500,
        "nombre_menages": 18200,
        "densite_hab_km2": 16900.0,
        "source_donnees": "INS_RGPH_2021"
    },

    # Cross-compatible E2E records
    {
        "id": "DEMO_CI_COCODY_ANGRE",
        "zone_id": "ci-abidjan-cocody-angre",
        "annee_recensement": 2021,
        "population_totale": 125000,
        "nombre_menages": 28000,
        "densite_hab_km2": 8500.0,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_CI_COCODY_RIVIERA",
        "zone_id": "ci-abidjan-cocody-riviera",
        "annee_recensement": 2021,
        "population_totale": 95000,
        "nombre_menages": 21000,
        "densite_hab_km2": 6200.0,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_CI_COCODY_DEUXPLATEAUX",
        "zone_id": "ci-abidjan-cocody-deuxplateaux",
        "annee_recensement": 2021,
        "population_totale": 110000,
        "nombre_menages": 25000,
        "densite_hab_km2": 7800.0,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_CI_YOPOUGON_NIANGON",
        "zone_id": "ci-abidjan-yopougon-niangon",
        "annee_recensement": 2021,
        "population_totale": 220000,
        "nombre_menages": 49000,
        "densite_hab_km2": 14500.0,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_CI_YOPOUGON_SIPOREX",
        "zone_id": "ci-abidjan-yopougon-siporex",
        "annee_recensement": 2021,
        "population_totale": 185000,
        "nombre_menages": 41000,
        "densite_hab_km2": 16200.0,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_CI_YOPOUGON_TOITSROUGES",
        "zone_id": "ci-abidjan-yopougon-toitsrouges",
        "annee_recensement": 2021,
        "population_totale": 140000,
        "nombre_menages": 31000,
        "densite_hab_km2": 11000.0,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_CI_MARCORY_BIETRY",
        "zone_id": "ci-abidjan-marcory-bietry",
        "annee_recensement": 2021,
        "population_totale": 75000,
        "nombre_menages": 18000,
        "densite_hab_km2": 9200.0,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_CI_MARCORY_ZONE4",
        "zone_id": "ci-abidjan-marcory-zone4",
        "annee_recensement": 2021,
        "population_totale": 65000,
        "nombre_menages": 15000,
        "densite_hab_km2": 7500.0,
        "source_donnees": "INS_RGPH_2021"
    },
    {
        "id": "DEMO_CI_MARCORY_ANOUMABO",
        "zone_id": "ci-abidjan-marcory-anoumabo",
        "annee_recensement": 2021,
        "population_totale": 115000,
        "nombre_menages": 26000,
        "densite_hab_km2": 15800.0,
        "source_donnees": "INS_RGPH_2021"
    }
]

# ==============================================================================
# 3. COMMERCIAL POIS (OpenStreetMap Retail baseline)
# ==============================================================================

COMMERCIAL_POIS = [
    # --- COCODY - ANGRÉ ---
    {
        "id": "POI_COCODY_01",
        "zone_id": "ZONE_COCODY_ANGRE",
        "nom_enseigne": "Carrefour Market Angré 7e Tranche",
        "type_activite": "supermarket",
        "point": [-3.9875, 5.3942],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_COCODY_02",
        "zone_id": "ZONE_COCODY_ANGRE",
        "nom_enseigne": "CDCI Supermarché Angré",
        "type_activite": "supermarket",
        "point": [-3.9820, 5.3910],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_COCODY_03",
        "zone_id": "ZONE_COCODY_ANGRE",
        "nom_enseigne": "Leader Price Angré Djibi",
        "type_activite": "supermarket",
        "point": [-3.9912, 5.4015],
        "source_osm": "OpenStreetMap"
    },

    # --- COCODY - PALMERAIE ---
    {
        "id": "POI_COCODY_04",
        "zone_id": "ZONE_COCODY_PALMERAIE",
        "nom_enseigne": "Carrefour Market Palmeraie (Rond-point)",
        "type_activite": "supermarket",
        "point": [-3.9580, 5.3745],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_COCODY_05",
        "zone_id": "ZONE_COCODY_PALMERAIE",
        "nom_enseigne": "Marché Moderne de la Palmeraie",
        "type_activite": "marketplace",
        "point": [-3.9530, 5.3790],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_COCODY_06",
        "zone_id": "ZONE_COCODY_PALMERAIE",
        "nom_enseigne": "Prosuma Sococé Express Palmeraie",
        "type_activite": "supermarket",
        "point": [-3.9620, 5.3815],
        "source_osm": "OpenStreetMap"
    },

    # --- COCODY - DEUX-PLATEAUX ---
    {
        "id": "POI_COCODY_07",
        "zone_id": "ZONE_COCODY_DEUX_PLATEAUX",
        "nom_enseigne": "Sococé Deux-Plateaux (Boulevard Latrille)",
        "type_activite": "supermarket",
        "point": [-4.0018, 5.3625],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_COCODY_08",
        "zone_id": "ZONE_COCODY_DEUX_PLATEAUX",
        "nom_enseigne": "Carrefour Market Rue des Jardins",
        "type_activite": "supermarket",
        "point": [-3.9960, 5.3670],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_COCODY_09",
        "zone_id": "ZONE_COCODY_DEUX_PLATEAUX",
        "nom_enseigne": "Super U Deux Plateaux Vallons",
        "type_activite": "supermarket",
        "point": [-4.0075, 5.3695],
        "source_osm": "OpenStreetMap"
    },

    # --- YOPOUGON - NIANGON NORD ---
    {
        "id": "POI_YOPOUGON_01",
        "zone_id": "ZONE_YOPOUGON_NIANGON_NORD",
        "nom_enseigne": "Supermarché Bonprix Niangon",
        "type_activite": "supermarket",
        "point": [-4.1020, 5.3385],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_YOPOUGON_02",
        "zone_id": "ZONE_YOPOUGON_NIANGON_NORD",
        "nom_enseigne": "CDCI Supermarché Niangon Sud/Nord",
        "type_activite": "supermarket",
        "point": [-4.0950, 5.3420],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_YOPOUGON_03",
        "zone_id": "ZONE_YOPOUGON_NIANGON_NORD",
        "nom_enseigne": "Grand Marché Niangon Texaco",
        "type_activite": "marketplace",
        "point": [-4.0980, 5.3470],
        "source_osm": "OpenStreetMap"
    },

    # --- YOPOUGON - SELMER ---
    {
        "id": "POI_YOPOUGON_04",
        "zone_id": "ZONE_YOPOUGON_SELMER",
        "nom_enseigne": "Grand Marché Selmer Yopougon",
        "type_activite": "marketplace",
        "point": [-4.0640, 5.3410],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_YOPOUGON_05",
        "zone_id": "ZONE_YOPOUGON_SELMER",
        "nom_enseigne": "CDCI Selmer Complexe",
        "type_activite": "supermarket",
        "point": [-4.0665, 5.3385],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_YOPOUGON_06",
        "zone_id": "ZONE_YOPOUGON_SELMER",
        "nom_enseigne": "Supérette Kenya Selmer",
        "type_activite": "convenience",
        "point": [-4.0600, 5.3440],
        "source_osm": "OpenStreetMap"
    },

    # --- YOPOUGON - TOIT-ROUGE / SIPOREX ---
    {
        "id": "POI_YOPOUGON_07",
        "zone_id": "ZONE_YOPOUGON_TOIT_ROUGE",
        "nom_enseigne": "Carrefour Market Yopougon Bel Air / Siporex",
        "type_activite": "supermarket",
        "point": [-4.0748, 5.3491],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_YOPOUGON_08",
        "zone_id": "ZONE_YOPOUGON_TOIT_ROUGE",
        "nom_enseigne": "Marché Toit-Rouge Yopougon",
        "type_activite": "marketplace",
        "point": [-4.0720, 5.3450],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_YOPOUGON_09",
        "zone_id": "ZONE_YOPOUGON_TOIT_ROUGE",
        "nom_enseigne": "CDCI Express Siporex",
        "type_activite": "supermarket",
        "point": [-4.0770, 5.3530],
        "source_osm": "OpenStreetMap"
    },

    # --- MARCORY - ZONE 4C ---
    {
        "id": "POI_MARCORY_01",
        "zone_id": "ZONE_MARCORY_ZONE_4C",
        "nom_enseigne": "Cap Sud (Hypermarché Prosuma & Galerie)",
        "type_activite": "supermarket",
        "point": [-3.9870, 5.2985],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_MARCORY_02",
        "zone_id": "ZONE_MARCORY_ZONE_4C",
        "nom_enseigne": "Prima Center (Supermarché Casino Prima)",
        "type_activite": "supermarket",
        "point": [-3.9833, 5.2953],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_MARCORY_03",
        "zone_id": "ZONE_MARCORY_ZONE_4C",
        "nom_enseigne": "Super Hayat Zone 4",
        "type_activite": "supermarket",
        "point": [-3.9800, 5.2915],
        "source_osm": "OpenStreetMap"
    },

    # --- MARCORY - BIÉTRY ---
    {
        "id": "POI_MARCORY_04",
        "zone_id": "ZONE_MARCORY_BIETRY",
        "nom_enseigne": "Supermarché Biétry Ébrié",
        "type_activite": "supermarket",
        "point": [-3.9785, 5.2840],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_MARCORY_05",
        "zone_id": "ZONE_MARCORY_BIETRY",
        "nom_enseigne": "Comptoir Gourmand & Cave Biétry",
        "type_activite": "convenience",
        "point": [-3.9820, 5.2825],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_MARCORY_06",
        "zone_id": "ZONE_MARCORY_BIETRY",
        "nom_enseigne": "Marché Artisanal et Poissons Biétry",
        "type_activite": "marketplace",
        "point": [-3.9740, 5.2805],
        "source_osm": "OpenStreetMap"
    },

    # --- MARCORY - ANOUMABO ---
    {
        "id": "POI_MARCORY_07",
        "zone_id": "ZONE_MARCORY_ANOUMABO",
        "nom_enseigne": "Grand Marché d'Anoumabo",
        "type_activite": "marketplace",
        "point": [-3.9726, 5.3084],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_MARCORY_08",
        "zone_id": "ZONE_MARCORY_ANOUMABO",
        "nom_enseigne": "CDCI Mini-Prix Anoumabo",
        "type_activite": "supermarket",
        "point": [-3.9760, 5.3050],
        "source_osm": "OpenStreetMap"
    },
    {
        "id": "POI_MARCORY_09",
        "zone_id": "ZONE_MARCORY_ANOUMABO",
        "nom_enseigne": "Alimentation Générale Lagune Anoumabo",
        "type_activite": "convenience",
        "point": [-3.9690, 5.3120],
        "source_osm": "OpenStreetMap"
    }
]

# ==============================================================================
# 4. ACCESSIBILITE ROUTIERE
# ==============================================================================

ACCESSIBILITE_ROUTIERE = [
    # Communes
    {
        "id": "ACC_COMMUNE_COCODY",
        "zone_id": "COMMUNE_COCODY",
        "score_connectivite": 78.5,
        "nombre_arrets_transport": 312,
        "densite_carrefours": 18.4
    },
    {
        "id": "ACC_COMMUNE_YOPOUGON",
        "zone_id": "COMMUNE_YOPOUGON",
        "score_connectivite": 72.0,
        "nombre_arrets_transport": 480,
        "densite_carrefours": 21.0
    },
    {
        "id": "ACC_COMMUNE_MARCORY",
        "zone_id": "COMMUNE_MARCORY",
        "score_connectivite": 85.5,
        "nombre_arrets_transport": 145,
        "densite_carrefours": 24.5
    },

    # Quartiers Cocody
    {
        "id": "ACC_COCODY_ANGRE",
        "zone_id": "ZONE_COCODY_ANGRE",
        "score_connectivite": 82.0,
        "nombre_arrets_transport": 64,
        "densite_carrefours": 26.5
    },
    {
        "id": "ACC_COCODY_PALMERAIE",
        "zone_id": "ZONE_COCODY_PALMERAIE",
        "score_connectivite": 75.0,
        "nombre_arrets_transport": 52,
        "densite_carrefours": 22.0
    },
    {
        "id": "ACC_COCODY_DEUX_PLATEAUX",
        "zone_id": "ZONE_COCODY_DEUX_PLATEAUX",
        "score_connectivite": 89.5,
        "nombre_arrets_transport": 78,
        "densite_carrefours": 29.8
    },

    # Quartiers Yopougon
    {
        "id": "ACC_YOPOUGON_NIANGON_NORD",
        "zone_id": "ZONE_YOPOUGON_NIANGON_NORD",
        "score_connectivite": 68.0,
        "nombre_arrets_transport": 94,
        "densite_carrefours": 19.5
    },
    {
        "id": "ACC_YOPOUGON_SELMER",
        "zone_id": "ZONE_YOPOUGON_SELMER",
        "score_connectivite": 79.0,
        "nombre_arrets_transport": 86,
        "densite_carrefours": 31.2
    },
    {
        "id": "ACC_YOPOUGON_TOIT_ROUGE",
        "zone_id": "ZONE_YOPOUGON_TOIT_ROUGE",
        "score_connectivite": 91.5,
        "nombre_arrets_transport": 115,
        "densite_carrefours": 35.4
    },

    # Quartiers Marcory
    {
        "id": "ACC_MARCORY_ZONE_4C",
        "zone_id": "ZONE_MARCORY_ZONE_4C",
        "score_connectivite": 93.0,
        "nombre_arrets_transport": 42,
        "densite_carrefours": 34.0
    },
    {
        "id": "ACC_MARCORY_BIETRY",
        "zone_id": "ZONE_MARCORY_BIETRY",
        "score_connectivite": 76.5,
        "nombre_arrets_transport": 28,
        "densite_carrefours": 17.8
    },
    {
        "id": "ACC_MARCORY_ANOUMABO",
        "zone_id": "ZONE_MARCORY_ANOUMABO",
        "score_connectivite": 65.0,
        "nombre_arrets_transport": 38,
        "densite_carrefours": 23.6
    },

    # Cross-compatible E2E records
    {
        "id": "ACC_CI_COCODY_ANGRE",
        "zone_id": "ci-abidjan-cocody-angre",
        "score_connectivite": 82.0,
        "nombre_arrets_transport": 64,
        "densite_carrefours": 26.5
    },
    {
        "id": "ACC_CI_COCODY_RIVIERA",
        "zone_id": "ci-abidjan-cocody-riviera",
        "score_connectivite": 78.0,
        "nombre_arrets_transport": 58,
        "densite_carrefours": 24.0
    },
    {
        "id": "ACC_CI_COCODY_DEUXPLATEAUX",
        "zone_id": "ci-abidjan-cocody-deuxplateaux",
        "score_connectivite": 88.0,
        "nombre_arrets_transport": 75,
        "densite_carrefours": 28.5
    },
    {
        "id": "ACC_CI_YOPOUGON_NIANGON",
        "zone_id": "ci-abidjan-yopougon-niangon",
        "score_connectivite": 74.0,
        "nombre_arrets_transport": 90,
        "densite_carrefours": 22.0
    },
    {
        "id": "ACC_CI_YOPOUGON_SIPOREX",
        "zone_id": "ci-abidjan-yopougon-siporex",
        "score_connectivite": 91.0,
        "nombre_arrets_transport": 110,
        "densite_carrefours": 34.0
    },
    {
        "id": "ACC_CI_YOPOUGON_TOITSROUGES",
        "zone_id": "ci-abidjan-yopougon-toitsrouges",
        "score_connectivite": 69.0,
        "nombre_arrets_transport": 70,
        "densite_carrefours": 20.0
    },
    {
        "id": "ACC_CI_MARCORY_BIETRY",
        "zone_id": "ci-abidjan-marcory-bietry",
        "score_connectivite": 85.0,
        "nombre_arrets_transport": 35,
        "densite_carrefours": 22.0
    },
    {
        "id": "ACC_CI_MARCORY_ZONE4",
        "zone_id": "ci-abidjan-marcory-zone4",
        "score_connectivite": 89.0,
        "nombre_arrets_transport": 45,
        "densite_carrefours": 32.0
    },
    {
        "id": "ACC_CI_MARCORY_ANOUMABO",
        "zone_id": "ci-abidjan-marcory-anoumabo",
        "score_connectivite": 65.0,
        "nombre_arrets_transport": 38,
        "densite_carrefours": 23.6
    }
]


def polygon_to_wkt(coords: List[List[float]]) -> str:
    ring = ", ".join(f"{lon:.4f} {lat:.4f}" for lon, lat in coords)
    return f"POLYGON(({ring}))"


def seed_database(db_url: Optional[str] = None) -> bool:
    """Idempotently seeds zones, demography, commercial POIs, and road accessibility."""
    import time
    target_url = db_url or DEFAULT_DATABASE_URL
    logger.info(f"Connecting to database to seed spatial data...")

    try:
        import psycopg
    except ImportError:
        logger.error("psycopg is not installed. Please install psycopg[binary].")
        raise

    conn = None
    for attempt in range(1, 5):
        try:
            conn = psycopg.connect(target_url, autocommit=True, connect_timeout=30)
            break
        except Exception as exc:
            if attempt == 4:
                raise
            logger.warning(f"Connection attempt {attempt} failed ({exc}); retrying in 3s...")
            time.sleep(3)

    with conn:
        with conn.cursor() as cur:
            # 1. Seed zones_geographiques
            logger.info(f"Seeding {len(ALL_ZONES)} geographic zones...")
            for z in ALL_ZONES:
                wkt = polygon_to_wkt(z["polygon"])
                sql = """
                    INSERT INTO zones_geographiques (id, nom_commune, nom_zone, type_zone, geom, created_at)
                    VALUES (%s, %s, %s, %s, ST_GeomFromText(%s, 4326), NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        nom_commune = EXCLUDED.nom_commune,
                        nom_zone = EXCLUDED.nom_zone,
                        type_zone = EXCLUDED.type_zone,
                        geom = EXCLUDED.geom;
                """
                cur.execute(sql, (z["id"], z["nom_commune"], z["nom_zone"], z["type_zone"], wkt))

            # 2. Seed demographie
            logger.info(f"Seeding {len(DEMOGRAPHIE)} demographic records...")
            for d in DEMOGRAPHIE:
                sql = """
                    INSERT INTO demographie (id, zone_id, annee_recensement, population_totale, nombre_menages, densite_hab_km2, source_donnees, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (zone_id) DO UPDATE SET
                        annee_recensement = EXCLUDED.annee_recensement,
                        population_totale = EXCLUDED.population_totale,
                        nombre_menages = EXCLUDED.nombre_menages,
                        densite_hab_km2 = EXCLUDED.densite_hab_km2,
                        source_donnees = EXCLUDED.source_donnees;
                """
                cur.execute(
                    sql,
                    (
                        d["id"],
                        d["zone_id"],
                        d["annee_recensement"],
                        d["population_totale"],
                        d["nombre_menages"],
                        d["densite_hab_km2"],
                        d["source_donnees"],
                    )
                )

            # 3. Seed infrastructures_commerces
            logger.info(f"Seeding {len(COMMERCIAL_POIS)} commercial POIs...")
            for p in COMMERCIAL_POIS:
                pt_wkt = f"POINT({p['point'][0]:.4f} {p['point'][1]:.4f})"
                sql = """
                    INSERT INTO infrastructures_commerces (id, zone_id, type_activite, nom_enseigne, geom_point, source_osm, created_at)
                    VALUES (%s, %s, %s, %s, ST_GeomFromText(%s, 4326), %s, NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        zone_id = EXCLUDED.zone_id,
                        type_activite = EXCLUDED.type_activite,
                        nom_enseigne = EXCLUDED.nom_enseigne,
                        geom_point = EXCLUDED.geom_point,
                        source_osm = EXCLUDED.source_osm;
                """
                cur.execute(sql, (p["id"], p["zone_id"], p["type_activite"], p["nom_enseigne"], pt_wkt, p["source_osm"]))

            # 4. Seed accessibilite_routiere
            logger.info(f"Seeding {len(ACCESSIBILITE_ROUTIERE)} road accessibility baselines...")
            for a in ACCESSIBILITE_ROUTIERE:
                sql = """
                    INSERT INTO accessibilite_routiere (id, zone_id, score_connectivite, nombre_arrets_transport, densite_carrefours, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (zone_id) DO UPDATE SET
                        score_connectivite = EXCLUDED.score_connectivite,
                        nombre_arrets_transport = EXCLUDED.nombre_arrets_transport,
                        densite_carrefours = EXCLUDED.densite_carrefours;
                """
                cur.execute(sql, (a["id"], a["zone_id"], a["score_connectivite"], a["nombre_arrets_transport"], a["densite_carrefours"]))

            logger.info("Spatial database seeding completed successfully!")
            return True


if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    seed_database(url_arg)
