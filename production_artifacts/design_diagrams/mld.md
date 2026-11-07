# Modèle Logique de Données (MLD) - Orange EcoMobility Intelligence (OEMI)

Ce document détaille la transposition relationnelle du MCD pour PostgreSQL / PostGIS.

---

## 1. Structure Relationnelle PostGIS

### `zones_geographiques` (Référentiel Spatial)
- `id` (VARCHAR(36), PK)
- `nom_commune` (VARCHAR(100), NOT NULL) — Ex: 'Cocody', 'Yopougon', 'Marcory'
- `nom_zone` (VARCHAR(150), NOT NULL) — Ex: 'Angré 7e Tranche', 'Zone 4C'
- `type_zone` (VARCHAR(50), NOT NULL) — Ex: 'Quartier', 'Zone Commerciale'
- `geom` (GEOMETRY(Polygon, 4326), NOT NULL) — Index spatial GiST
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW())

### `mobilite_agregee` (Historique & Séries Temporelles de Présence)
- `id` (VARCHAR(36), PK)
- `zone_id` (VARCHAR(36), FK -> `zones_geographiques.id`, NOT NULL)
- `date_observation` (DATE, NOT NULL)
- `plage_horaire` (VARCHAR(20), NOT NULL) — Ex: '08h-10h', '12h-14h', '18h-20h'
- `volume_presence` (FLOAT, NOT NULL)
- `flux_entrants` (FLOAT)
- `flux_sortants` (FLOAT)
- `est_synthetique` (BOOLEAN, DEFAULT FALSE)
- `seuil_k_anonymat_valide` (BOOLEAN, DEFAULT TRUE)
- *Index* : `(zone_id, date_observation, plage_horaire)`

### `demographie` (Données INS / RGPH 2021)
- `id` (VARCHAR(36), PK)
- `zone_id` (VARCHAR(36), FK -> `zones_geographiques.id`, UNIQUE, NOT NULL)
- `annee_recensement` (INT, DEFAULT 2021)
- `population_totale` (INT, NOT NULL)
- `nombre_menages` (INT)
- `densite_hab_km2` (FLOAT)
- `source_donnees` (VARCHAR(100), DEFAULT 'INS_RGPH_2021')

### `infrastructures_commerces` (Données OSM & Concurrence)
- `id` (VARCHAR(36), PK)
- `zone_id` (VARCHAR(36), FK -> `zones_geographiques.id`, NOT NULL)
- `type_activite` (VARCHAR(100), NOT NULL) — Ex: 'supermarket', 'convenience', 'marketplace'
- `nom_enseigne` (VARCHAR(150))
- `geom_point` (GEOMETRY(Point, 4326), NOT NULL) — Index spatial GiST
- `source_osm` (VARCHAR(100), DEFAULT 'OpenStreetMap')

### `accessibilite_routiere` (Connectivité & Transports)
- `id` (VARCHAR(36), PK)
- `zone_id` (VARCHAR(36), FK -> `zones_geographiques.id`, UNIQUE, NOT NULL)
- `score_connectivite` (FLOAT, CHECK (score_connectivite BETWEEN 0 AND 100))
- `nombre_arrets_transport` (INT, DEFAULT 0)
- `densite_carrefours` (FLOAT)

### `previsions_frequentation` (Résultats Modèles IA)
- `id` (VARCHAR(36), PK)
- `zone_id` (VARCHAR(36), FK -> `zones_geographiques.id`, NOT NULL)
- `date_horizon` (TIMESTAMP WITH TIME ZONE, NOT NULL)
- `valeur_estimee` (FLOAT, NOT NULL)
- `borne_inferieure` (FLOAT)
- `borne_superieure` (FLOAT)
- `modele_utilise` (VARCHAR(50), NOT NULL) — 'NAIVE_D7', 'PROPHET', 'XGBOOST'
- `metrique_wape` (FLOAT)
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW())

### `scores_recommandations_ipet` (Moteur de Décision)
- `id` (VARCHAR(36), PK)
- `zone_id` (VARCHAR(36), FK -> `zones_geographiques.id`, NOT NULL)
- `secteur_cible` (VARCHAR(50), DEFAULT 'SUPERMARCHE')
- `score_ipet` (FLOAT, NOT NULL, CHECK (score_ipet BETWEEN 0 AND 100))
- `rang_classement` (INT, NOT NULL)
- `facteurs_positifs` (JSONB)
- `facteurs_limitants` (JSONB)
- `taux_completude` (FLOAT)
- `version_modele` (VARCHAR(20), DEFAULT 'v1.0')
- `calcule_le` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW())

### `utilisateurs` & `journaux_audit` (Sécurité & Traçabilité)
- `utilisateurs` : `id`, `email`, `role` ('ADMIN', 'ANALYSTE', 'METIER'), `password_hash`, `created_at`
- `journaux_audit` : `id`, `utilisateur_id` (FK), `action_type` ('CONSULTATION', 'EXPORT_PDF', 'EXPORT_EXCEL'), `zone_concernee`, `horodatage`, `parametres_filtres` (JSONB)
