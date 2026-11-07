"""
backend/app/db/init_db.py
Idempotent Database Initialization for Neon PostgreSQL & PostGIS.
Enables PostGIS extension, creates all 9 MLD tables with GiST indexes and constraints.
"""

import os
import sys
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("oemi.init_db")

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_4kz7aAUJPblS@ep-cold-sea-bdkcgioc.c-8.us-east-2.aws.neon.tech:5432/neondb?sslmode=require"
)

DDL_STATEMENTS = [
    # 0. Spatial PostGIS Extension
    "CREATE EXTENSION IF NOT EXISTS postgis;",

    # 1. zones_geographiques (Referentiel Spatial Communal & Quartiers)
    """
    CREATE TABLE IF NOT EXISTS zones_geographiques (
        id VARCHAR(36) PRIMARY KEY,
        nom_commune VARCHAR(100) NOT NULL,
        nom_zone VARCHAR(150) NOT NULL,
        type_zone VARCHAR(50) NOT NULL,
        geom GEOMETRY(Polygon, 4326) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_zones_geographiques_geom ON zones_geographiques USING GIST (geom);",
    "CREATE INDEX IF NOT EXISTS idx_zones_geographiques_commune ON zones_geographiques (nom_commune);",
    "CREATE INDEX IF NOT EXISTS idx_zones_geographiques_type ON zones_geographiques (type_zone);",

    # 2. mobilite_agregee (Historique & Series Temporelles de Presence)
    """
    CREATE TABLE IF NOT EXISTS mobilite_agregee (
        id VARCHAR(36) PRIMARY KEY,
        zone_id VARCHAR(36) NOT NULL REFERENCES zones_geographiques(id) ON DELETE CASCADE,
        date_observation DATE NOT NULL,
        plage_horaire VARCHAR(20) NOT NULL,
        volume_presence DOUBLE PRECISION,
        flux_entrants DOUBLE PRECISION DEFAULT 0.0,
        flux_sortants DOUBLE PRECISION DEFAULT 0.0,
        est_synthetique BOOLEAN DEFAULT FALSE NOT NULL,
        seuil_k_anonymat_valide BOOLEAN DEFAULT TRUE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        CONSTRAINT uq_mobilite_zone_date_plage UNIQUE (zone_id, date_observation, plage_horaire)
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_mobilite_zone_date_plage ON mobilite_agregee (zone_id, date_observation, plage_horaire);",
    "CREATE INDEX IF NOT EXISTS idx_mobilite_date ON mobilite_agregee (date_observation);",
    "CREATE INDEX IF NOT EXISTS idx_mobilite_k_anonymat ON mobilite_agregee (seuil_k_anonymat_valide);",

    # 3. demographie (Donnees INS / RGPH 2021)
    """
    CREATE TABLE IF NOT EXISTS demographie (
        id VARCHAR(36) PRIMARY KEY,
        zone_id VARCHAR(36) NOT NULL UNIQUE REFERENCES zones_geographiques(id) ON DELETE CASCADE,
        annee_recensement INT DEFAULT 2021 NOT NULL,
        population_totale INT NOT NULL,
        nombre_menages INT,
        densite_hab_km2 DOUBLE PRECISION,
        source_donnees VARCHAR(100) DEFAULT 'INS_RGPH_2021' NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,

    # 4. infrastructures_commerces (Points d'Interet Commerciaux OSM)
    """
    CREATE TABLE IF NOT EXISTS infrastructures_commerces (
        id VARCHAR(36) PRIMARY KEY,
        zone_id VARCHAR(36) NOT NULL REFERENCES zones_geographiques(id) ON DELETE CASCADE,
        type_activite VARCHAR(100) NOT NULL,
        nom_enseigne VARCHAR(150),
        geom_point GEOMETRY(Point, 4326) NOT NULL,
        source_osm VARCHAR(100) DEFAULT 'OpenStreetMap' NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_infra_geom_point ON infrastructures_commerces USING GIST (geom_point);",
    "CREATE INDEX IF NOT EXISTS idx_infra_zone_id ON infrastructures_commerces (zone_id);",
    "CREATE INDEX IF NOT EXISTS idx_infra_type_activite ON infrastructures_commerces (type_activite);",

    # 5. accessibilite_routiere (Connectivite & Transports)
    """
    CREATE TABLE IF NOT EXISTS accessibilite_routiere (
        id VARCHAR(36) PRIMARY KEY,
        zone_id VARCHAR(36) NOT NULL UNIQUE REFERENCES zones_geographiques(id) ON DELETE CASCADE,
        score_connectivite DOUBLE PRECISION CHECK (score_connectivite BETWEEN 0 AND 100),
        nombre_arrets_transport INT DEFAULT 0 NOT NULL,
        densite_carrefours DOUBLE PRECISION,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,

    # 6. previsions_frequentation (Resultats Modeles IA - D-7, Prophet, XGBoost)
    """
    CREATE TABLE IF NOT EXISTS previsions_frequentation (
        id VARCHAR(36) PRIMARY KEY,
        zone_id VARCHAR(36) NOT NULL REFERENCES zones_geographiques(id) ON DELETE CASCADE,
        date_horizon TIMESTAMP WITH TIME ZONE NOT NULL,
        valeur_estimee DOUBLE PRECISION NOT NULL,
        borne_inferieure DOUBLE PRECISION,
        borne_superieure DOUBLE PRECISION,
        modele_utilise VARCHAR(50) NOT NULL CHECK (modele_utilise IN ('NAIVE_D7', 'PROPHET', 'XGBOOST')),
        metrique_wape DOUBLE PRECISION,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_previsions_zone_modele_date ON previsions_frequentation (zone_id, modele_utilise, date_horizon);",
    "CREATE INDEX IF NOT EXISTS idx_previsions_modele ON previsions_frequentation (modele_utilise);",

    # 7. scores_recommandations_ipet (Moteur Decisionnel IPET)
    """
    CREATE TABLE IF NOT EXISTS scores_recommandations_ipet (
        id VARCHAR(36) PRIMARY KEY,
        zone_id VARCHAR(36) NOT NULL REFERENCES zones_geographiques(id) ON DELETE CASCADE,
        secteur_cible VARCHAR(50) DEFAULT 'SUPERMARCHE' NOT NULL,
        score_ipet DOUBLE PRECISION NOT NULL CHECK (score_ipet BETWEEN 0 AND 100),
        rang_classement INT NOT NULL,
        facteurs_positifs JSONB DEFAULT '[]'::jsonb,
        facteurs_limitants JSONB DEFAULT '[]'::jsonb,
        taux_completude DOUBLE PRECISION DEFAULT 1.0 CHECK (taux_completude BETWEEN 0 AND 1),
        version_modele VARCHAR(20) DEFAULT 'v1.0' NOT NULL,
        calcule_le TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_ipet_zone_secteur ON scores_recommandations_ipet (zone_id, secteur_cible);",
    "CREATE INDEX IF NOT EXISTS idx_ipet_score ON scores_recommandations_ipet (score_ipet DESC);",
    "CREATE INDEX IF NOT EXISTS idx_ipet_rang ON scores_recommandations_ipet (rang_classement ASC);",

    # 8. utilisateurs (Authentification & Roles RBAC)
    """
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id VARCHAR(36) PRIMARY KEY,
        email VARCHAR(255) NOT NULL UNIQUE,
        role VARCHAR(50) NOT NULL CHECK (role IN ('ADMIN', 'ANALYSTE', 'METIER')),
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_utilisateurs_email ON utilisateurs (email);",

    # 9. journaux_audit (Tracabilite & Securite)
    """
    CREATE TABLE IF NOT EXISTS journaux_audit (
        id VARCHAR(36) PRIMARY KEY,
        utilisateur_id VARCHAR(36) REFERENCES utilisateurs(id) ON DELETE SET NULL,
        action_type VARCHAR(50) NOT NULL CHECK (action_type IN ('CONSULTATION', 'EXPORT_PDF', 'EXPORT_EXCEL', 'CALCUL_IPET', 'LOGIN', 'LOGOUT')),
        zone_concernee VARCHAR(150),
        horodatage TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        parametres_filtres JSONB DEFAULT '{}'::jsonb
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_audit_horodatage ON journaux_audit (horodatage DESC);",
    "CREATE INDEX IF NOT EXISTS idx_audit_utilisateur ON journaux_audit (utilisateur_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_action ON journaux_audit (action_type);",

    # Ensure created_at / horodatage / calcule_le timestamp columns exist with DEFAULT NOW()
    "ALTER TABLE zones_geographiques ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
    "ALTER TABLE zones_geographiques ALTER COLUMN created_at SET DEFAULT NOW();",
    "ALTER TABLE demographie ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
    "ALTER TABLE demographie ALTER COLUMN created_at SET DEFAULT NOW();",
    "ALTER TABLE infrastructures_commerces ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
    "ALTER TABLE infrastructures_commerces ALTER COLUMN created_at SET DEFAULT NOW();",
    "ALTER TABLE accessibilite_routiere ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
    "ALTER TABLE accessibilite_routiere ALTER COLUMN created_at SET DEFAULT NOW();",
    "ALTER TABLE mobilite_agregee ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
    "ALTER TABLE mobilite_agregee ALTER COLUMN created_at SET DEFAULT NOW();",
    "ALTER TABLE previsions_frequentation ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
    "ALTER TABLE scores_recommandations_ipet ADD COLUMN IF NOT EXISTS calcule_le TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
    "ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
    "ALTER TABLE journaux_audit ADD COLUMN IF NOT EXISTS horodatage TIMESTAMP WITH TIME ZONE DEFAULT NOW();"
]


def init_database(db_url: Optional[str] = None) -> bool:
    """Connects to Neon PostgreSQL and executes DDL to create PostGIS schema idempotently."""
    import time
    target_url = db_url or DEFAULT_DATABASE_URL
    logger.info("Connecting to Neon PostgreSQL...")

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
            cur.execute("SELECT version();")
            pg_ver = cur.fetchone()[0]
            logger.info(f"Connected to: {pg_ver}")

            # Verify PostGIS
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            cur.execute("SELECT PostGIS_Full_Version();")
            postgis_ver = cur.fetchone()[0]
            logger.info(f"PostGIS Version: {postgis_ver}")

            # Execute DDL
            for idx, stmt in enumerate(DDL_STATEMENTS, start=1):
                cur.execute(stmt)

            logger.info("Successfully executed all 9 table DDL definitions and GiST indexes.")
            return True


if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    init_database(url_arg)
