"""
backend/tests/test_db_spatial.py
Pytest suite for Neon Cloud PostgreSQL/PostGIS connectivity, 9-table schema verification,
GiST spatial indexes, PostGIS spatial queries (ST_Within, ST_Contains), and check constraints.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from sqlalchemy import text, select
from app.db.session import engine, SessionLocal
from app.models.zone import ZoneGeographique
from app.models.demography import Demographie
from app.models.infrastructure import InfrastructureCommerce, AccessibiliteRoutiere
from app.models.ipet import ScoreRecommandationIPET
from app.models.mobility import MobiliteAgregee
from app.models.prediction import PrevisionFrequentation
from app.models.audit import Utilisateur, JournalAudit


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional session fixture."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_database_connectivity():
    """Verifies successful connection to Neon PostgreSQL."""
    with engine.connect() as conn:
        res = conn.execute(text("SELECT 1;")).scalar()
        assert res == 1


def test_postgis_extension_active():
    """Verifies that PostGIS 3.6+ is enabled and functional."""
    with engine.connect() as conn:
        version = conn.execute(text("SELECT postgis_lib_version();")).scalar()
        assert version is not None
        assert version.startswith("3.")


def test_all_9_tables_exist():
    """Verifies that all 9 OEMI tables exist in the public schema."""
    expected_tables = {
        "zones_geographiques",
        "mobilite_agregee",
        "demographie",
        "infrastructures_commerces",
        "accessibilite_routiere",
        "previsions_frequentation",
        "scores_recommandations_ipet",
        "utilisateurs",
        "journaux_audit",
    }
    with engine.connect() as conn:
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        existing_tables = set(conn.execute(query).scalars().all())
        missing = expected_tables - existing_tables
        assert not missing, f"Missing tables in database: {missing}"


def test_spatial_gist_indexes_exist():
    """Verifies that GiST spatial indexes exist on spatial geometry columns."""
    with engine.connect() as conn:
        query = text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
              AND indexname IN ('idx_zones_geographiques_geom', 'idx_infrastructures_commerces_geom_point');
        """)
        indexes = set(conn.execute(query).scalars().all())
        assert "idx_zones_geographiques_geom" in indexes
        assert "idx_infrastructures_commerces_geom_point" in indexes


def test_seeded_zones_integrity(db_session):
    """Verifies that all 9 pilot zones for Cocody, Yopougon, and Marcory are seeded."""
    zones = db_session.execute(select(ZoneGeographique)).scalars().all()
    assert len(zones) >= 9

    communes = {z.nom_commune for z in zones}
    assert "Cocody" in communes
    assert "Yopougon" in communes
    assert "Marcory" in communes


def test_postgis_spatial_containment(db_session):
    """Verifies PostGIS ST_Within spatial containment between commercial POIs and zones."""
    with engine.connect() as conn:
        query = text("""
            SELECT ST_Within(p.geom_point, z.geom)
            FROM infrastructures_commerces p
            JOIN zones_geographiques z ON p.zone_id = z.id
            WHERE p.id = 'poi-carrefour-playce-palmeraie';
        """)
        is_inside = conn.execute(query).scalar()
        assert is_inside is True, "POI PlaYce Palmeraie should be spatially inside its zone"


def test_postgis_spatial_probe_functions():
    """Verifies PostGIS geometry generation, centroid, and area calculations."""
    with engine.connect() as conn:
        query = text("""
            SELECT 
                ST_GeometryType(geom) AS geom_type,
                ST_SRID(geom) AS srid,
                ST_Area(ST_Transform(geom, 32630)) AS area_m2
            FROM zones_geographiques
            WHERE id = 'ci-abidjan-cocody-angre';
        """)
        row = conn.execute(query).fetchone()
        assert row is not None
        assert row[0] == "ST_Polygon"
        assert row[1] == 4326
        assert row[2] > 1_000_000


def test_ipet_score_check_constraint(db_session):
    """Verifies that check constraint chk_ipet_score_range prevents IPET scores outside [0, 100]."""
    with pytest.raises(Exception):
        invalid_ipet = ScoreRecommandationIPET(
            zone_id="ci-abidjan-cocody-angre",
            secteur_cible="SUPERMARCHE",
            score_ipet=125.0,  # Invalid: > 100
            rang_classement=1,
            facteurs_positifs=[],
            facteurs_limitants=[]
        )
        db_session.add(invalid_ipet)
        db_session.commit()
    db_session.rollback()


def test_accessibility_score_check_constraint(db_session):
    """Verifies that check constraint chk_connectivite_range prevents scores outside [0, 100]."""
    with pytest.raises(Exception):
        invalid_access = AccessibiliteRoutiere(
            zone_id="ci-abidjan-cocody-angre",
            score_connectivite=-10.0,  # Invalid: < 0
            nombre_arrets_transport=5,
            densite_carrefours=2.0
        )
        db_session.add(invalid_access)
        db_session.commit()
    db_session.rollback()
