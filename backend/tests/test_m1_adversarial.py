"""
backend/tests/test_m1_adversarial.py
Adversarial Stress Test Suite for Milestone 1: Database & Spatial Infrastructure.

Empirical verification harness targeting:
1. Check constraint fuzzing:
   - score_ipet = 100.1, score_ipet = -0.1 strictly raise CheckViolation
   - score_connectivite = 150, score_connectivite = -0.1, score_connectivite = 100.1 strictly raise CheckViolation
   - score_ipet = 0.0 and score_ipet = 100.0 (boundary acceptance)
   - Invalid model, role, and audit action constraints
2. Spatial validity stress tests:
   - ST_IsValid(geom) == True for all 9 seeded zones
   - ST_SRID(geom) == 4326 for all 9 seeded zones
   - ST_GeometryType(geom) == 'ST_Polygon' for all 9 seeded zones
   - ST_Contains(zone.geom, poi.geom_point) on live database POIs
   - Cross-commune spatial discrimination (negative containment)
3. Idempotency stress tests:
   - init_database() execution safety on live DB
   - seed_zones() re-execution safety and zero-duplicate guarantees
"""

import sys
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from sqlalchemy import text, select, func
from sqlalchemy.exc import IntegrityError
from app.db.session import engine, SessionLocal
from app.db.init_db import init_database
from app.seeds.seed_zones import seed_zones, ZONES_DATA, POIS_DATA
from app.models.zone import ZoneGeographique
from app.models.demography import Demographie
from app.models.infrastructure import InfrastructureCommerce, AccessibiliteRoutiere
from app.models.ipet import ScoreRecommandationIPET
from app.models.prediction import PrevisionFrequentation
from app.models.audit import Utilisateur, JournalAudit

# 9 official sub-zone IDs for Milestone 1
PILOT_ZONE_IDS = [z["id"] for z in ZONES_DATA]
PILOT_POI_IDS = [p["id"] for p in POIS_DATA]


@pytest.fixture(scope="function")
def db_session():
    """Provides a transactional database session fixture with retries."""
    session = None
    for attempt in range(5):
        try:
            session = SessionLocal()
            session.execute(text("SELECT 1;"))
            break
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2)
    try:
        yield session
    finally:
        if session:
            session.close()


def _is_check_violation(exc_info) -> bool:
    """Verifies that an IntegrityError originates from a database CHECK constraint violation."""
    err_str = str(exc_info.value).lower()
    orig = getattr(exc_info.value, "orig", None)
    orig_name = orig.__class__.__name__.lower() if orig else ""
    return (
        "checkviolation" in orig_name
        or "check constraint" in err_str
        or "chk_" in err_str
        or "violates check constraint" in err_str
    )


# ==============================================================================
# 1. CHECK CONSTRAINT FUZZING
# ==============================================================================

class TestCheckConstraintFuzzing:
    """Fuzzes numerical and enumeration check constraints with adversarial out-of-bound inputs."""

    def test_ipet_score_100_1_overflow_rejected(self, db_session):
        """Verifies that inserting score_ipet = 100.1 strictly raises CheckViolation."""
        invalid_ipet = ScoreRecommandationIPET(
            id=f"adv-ipet-over-{uuid.uuid4().hex[:8]}",
            zone_id="ci-abidjan-cocody-angre",
            secteur_cible="SUPERMARCHE",
            score_ipet=100.1,  # Adversarial upper overflow
            rang_classement=1,
            facteurs_positifs=[],
            facteurs_limitants=[]
        )
        with pytest.raises(IntegrityError) as exc_info:
            db_session.add(invalid_ipet)
            db_session.commit()
        db_session.rollback()
        assert _is_check_violation(exc_info), f"Expected CheckViolation, got: {exc_info.value}"

    def test_ipet_score_negative_0_1_overflow_rejected(self, db_session):
        """Verifies that inserting score_ipet = -0.1 strictly raises CheckViolation."""
        invalid_ipet = ScoreRecommandationIPET(
            id=f"adv-ipet-neg-{uuid.uuid4().hex[:8]}",
            zone_id="ci-abidjan-cocody-angre",
            secteur_cible="SUPERMARCHE",
            score_ipet=-0.1,  # Adversarial negative overflow
            rang_classement=1,
            facteurs_positifs=[],
            facteurs_limitants=[]
        )
        with pytest.raises(IntegrityError) as exc_info:
            db_session.add(invalid_ipet)
            db_session.commit()
        db_session.rollback()
        assert _is_check_violation(exc_info), f"Expected CheckViolation, got: {exc_info.value}"

    def test_ipet_score_boundaries_accepted(self, db_session):
        """Verifies that exact boundary values score_ipet = 0.0 and score_ipet = 100.0 are accepted."""
        ipet_min = ScoreRecommandationIPET(
            id=f"adv-ipet-min-{uuid.uuid4().hex[:8]}",
            zone_id="ci-abidjan-cocody-angre",
            secteur_cible="SUPERMARCHE",
            score_ipet=0.0,  # Boundary min
            rang_classement=9,
            facteurs_positifs=[{"nom": "F0", "poids": 0.0}],
            facteurs_limitants=[{"nom": "F_all", "poids": 1.0}]
        )
        ipet_max = ScoreRecommandationIPET(
            id=f"adv-ipet-max-{uuid.uuid4().hex[:8]}",
            zone_id="ci-abidjan-cocody-angre",
            secteur_cible="SUPERMARCHE",
            score_ipet=100.0,  # Boundary max
            rang_classement=1,
            facteurs_positifs=[{"nom": "F_perfect", "poids": 1.0}],
            facteurs_limitants=[]
        )
        try:
            db_session.add(ipet_min)
            db_session.add(ipet_max)
            db_session.commit()

            saved_min = db_session.get(ScoreRecommandationIPET, ipet_min.id)
            saved_max = db_session.get(ScoreRecommandationIPET, ipet_max.id)
            assert saved_min is not None and saved_min.score_ipet == 0.0
            assert saved_max is not None and saved_max.score_ipet == 100.0
        finally:
            db_session.rollback()
            db_session.execute(
                text("DELETE FROM scores_recommandations_ipet WHERE id IN (:id1, :id2)"),
                {"id1": ipet_min.id, "id2": ipet_max.id}
            )
            db_session.commit()

    def test_connectivity_score_150_overflow_rejected(self, db_session):
        """Verifies that setting score_connectivite = 150 strictly raises CheckViolation."""
        with pytest.raises(IntegrityError) as exc_info:
            db_session.execute(
                text("UPDATE accessibilite_routiere SET score_connectivite = 150 WHERE zone_id = 'ci-abidjan-cocody-angre'")
            )
            db_session.commit()
        db_session.rollback()
        assert _is_check_violation(exc_info), f"Expected CheckViolation for 150, got: {exc_info.value}"

    def test_connectivity_score_negative_rejected(self, db_session):
        """Verifies that setting score_connectivite = -0.1 strictly raises CheckViolation."""
        with pytest.raises(IntegrityError) as exc_info:
            db_session.execute(
                text("UPDATE accessibilite_routiere SET score_connectivite = -0.1 WHERE zone_id = 'ci-abidjan-cocody-angre'")
            )
            db_session.commit()
        db_session.rollback()
        assert _is_check_violation(exc_info), f"Expected CheckViolation for -0.1, got: {exc_info.value}"

    def test_connectivity_score_100_1_rejected(self, db_session):
        """Verifies that setting score_connectivite = 100.1 strictly raises CheckViolation."""
        with pytest.raises(IntegrityError) as exc_info:
            db_session.execute(
                text("UPDATE accessibilite_routiere SET score_connectivite = 100.1 WHERE zone_id = 'ci-abidjan-cocody-angre'")
            )
            db_session.commit()
        db_session.rollback()
        assert _is_check_violation(exc_info), f"Expected CheckViolation for 100.1, got: {exc_info.value}"

    def test_prediction_invalid_model_rejected(self, db_session):
        """Verifies that inserting an unapproved ML model strictly raises CheckViolation."""
        invalid_pred = PrevisionFrequentation(
            id=f"adv-pred-{uuid.uuid4().hex[:8]}",
            zone_id="ci-abidjan-cocody-angre",
            date_horizon=datetime.now(timezone.utc),
            valeur_estimee=500.0,
            modele_utilise="ARIMA"
        )
        with pytest.raises(IntegrityError) as exc_info:
            db_session.add(invalid_pred)
            db_session.commit()
        db_session.rollback()
        assert _is_check_violation(exc_info), f"Expected CheckViolation for ARIMA model, got: {exc_info.value}"

    def test_user_invalid_role_rejected(self, db_session):
        """Verifies that inserting an invalid user role strictly raises CheckViolation."""
        invalid_user = Utilisateur(
            id=f"adv-usr-{uuid.uuid4().hex[:8]}",
            email=f"hacker_{uuid.uuid4().hex[:6]}@example.com",
            role="SUPERADMIN",
            password_hash="fake_hash"
        )
        with pytest.raises(IntegrityError) as exc_info:
            db_session.add(invalid_user)
            db_session.commit()
        db_session.rollback()
        assert _is_check_violation(exc_info), f"Expected CheckViolation for role, got: {exc_info.value}"

    def test_audit_invalid_action_rejected(self, db_session):
        """Verifies that inserting an unapproved audit action strictly raises CheckViolation."""
        invalid_audit = JournalAudit(
            id=f"adv-aud-{uuid.uuid4().hex[:8]}",
            action_type="DROP_DATABASE",
            zone_concernee="All"
        )
        with pytest.raises(IntegrityError) as exc_info:
            db_session.add(invalid_audit)
            db_session.commit()
        db_session.rollback()
        assert _is_check_violation(exc_info), f"Expected CheckViolation for audit action, got: {exc_info.value}"


# ==============================================================================
# 2. SPATIAL VALIDITY & POSTGIS INTEGRITY STRESS TESTS
# ==============================================================================

class TestSpatialValidityStress:
    """Stress tests geometric validity, projection SRID, topological closure, and spatial containment."""

    def test_all_9_seeded_zones_geometric_validity(self, db_session):
        """Verifies that ST_IsValid(geom) is True and ST_IsValidReason is 'Valid Geometry' for all 9 seeded zones."""
        query = text("""
            SELECT 
                id, 
                nom_commune, 
                nom_zone, 
                ST_IsValid(geom) AS is_valid,
                ST_IsValidReason(geom) AS valid_reason,
                ST_SRID(geom) AS srid,
                ST_GeometryType(geom) AS geom_type,
                ST_NPoints(geom) AS num_points,
                ST_IsClosed(ST_Boundary(geom)) AS is_closed
            FROM zones_geographiques
            WHERE id IN :zone_ids
            ORDER BY nom_commune, nom_zone;
        """)
        rows = db_session.execute(query, {"zone_ids": tuple(PILOT_ZONE_IDS)}).fetchall()
        assert len(rows) == 9, f"Expected 9 seeded pilot zones, found {len(rows)}"

        for row in rows:
            zone_desc = f"{row.nom_commune} / {row.nom_zone} ({row.id})"
            assert row.is_valid is True, f"Geometry invalid for zone {zone_desc}: {row.valid_reason}"
            assert row.valid_reason == "Valid Geometry", f"Invalid reason for {zone_desc}: {row.valid_reason}"
            assert row.srid == 4326, f"Incorrect SRID for {zone_desc}: got {row.srid}, expected 4326"
            assert row.geom_type == "ST_Polygon", f"Incorrect geometry type for {zone_desc}: {row.geom_type}"
            assert row.num_points >= 4, f"Insufficient points in polygon for {zone_desc}: {row.num_points}"
            assert row.is_closed is True, f"Polygon boundary is not closed for {zone_desc}"

    def test_all_13_seeded_pois_geometric_validity(self, db_session):
        """Verifies that all 13 seeded commercial POIs have valid Point geometries and SRID 4326."""
        query = text("""
            SELECT 
                id, 
                nom_enseigne, 
                ST_IsValid(geom_point) AS is_valid,
                ST_SRID(geom_point) AS srid,
                ST_GeometryType(geom_point) AS geom_type,
                ST_X(geom_point) AS lon,
                ST_Y(geom_point) AS lat
            FROM infrastructures_commerces
            WHERE id IN :poi_ids;
        """)
        rows = db_session.execute(query, {"poi_ids": tuple(PILOT_POI_IDS)}).fetchall()
        assert len(rows) == 13, f"Expected 13 seeded commercial POIs, found {len(rows)}"

        for row in rows:
            poi_desc = f"{row.nom_enseigne} ({row.id})"
            assert row.is_valid is True, f"Invalid point geometry for POI {poi_desc}"
            assert row.srid == 4326, f"Incorrect SRID for POI {poi_desc}: {row.srid}"
            assert row.geom_type == "ST_Point", f"Incorrect geom_type for POI {poi_desc}: {row.geom_type}"
            assert -4.3 <= row.lon <= -3.8, f"Longitude out of Abidjan range for {poi_desc}: {row.lon}"
            assert 5.2 <= row.lat <= 5.5, f"Latitude out of Abidjan range for {poi_desc}: {row.lat}"

    def test_postgis_spatial_containment_on_live_db(self, db_session):
        """
        Adversarial test: Checks whether ST_Contains(z.geom, p.geom_point) holds on the live database.
        Detects geometry desynchronization between seed_zones.py and live Neon table.
        """
        query = text("""
            SELECT 
                p.id AS poi_id,
                p.nom_enseigne,
                z.id AS zone_id,
                z.nom_commune,
                z.nom_zone,
                ST_Contains(z.geom, p.geom_point) AS is_contained,
                ST_Within(p.geom_point, z.geom) AS is_within,
                ST_Distance(z.geom, p.geom_point) AS dist
            FROM infrastructures_commerces p
            JOIN zones_geographiques z ON p.zone_id = z.id
            WHERE p.id IN :poi_ids;
        """)
        rows = db_session.execute(query, {"poi_ids": tuple(PILOT_POI_IDS)}).fetchall()
        assert len(rows) == 13, f"Expected 13 POI containment evaluations, got {len(rows)}"

        failed_containment = [
            f"POI '{r.nom_enseigne}' ({r.poi_id}) in zone '{r.nom_zone}' (dist={r.dist})"
            for r in rows if not r.is_contained
        ]
        assert not failed_containment, (
            f"SPATIAL CONTAINMENT FAILED on live database for {len(failed_containment)} POIs:\n"
            + "\n".join(failed_containment)
            + "\nRoot cause: Geometry in database does not match intended polygon from seed_zones.py!"
        )

    def test_adversarial_cross_commune_negative_containment(self, db_session):
        """
        Adversarial test: Ensures that commercial POIs in Cocody are NEVER contained in
        Yopougon or Marcory zones. Validates spatial discrimination accuracy of PostGIS.
        """
        query = text("""
            SELECT 
                p.nom_enseigne,
                z.nom_commune AS foreign_commune,
                z.nom_zone AS foreign_zone,
                ST_Contains(z.geom, p.geom_point) AS false_containment
            FROM infrastructures_commerces p
            JOIN zones_geographiques pz ON p.zone_id = pz.id
            CROSS JOIN zones_geographiques z
            WHERE pz.nom_commune = 'Cocody'
              AND z.nom_commune IN ('Yopougon', 'Marcory')
              AND p.id IN :poi_ids;
        """)
        rows = db_session.execute(query, {"poi_ids": tuple(PILOT_POI_IDS)}).fetchall()
        assert len(rows) > 0, "No cross-commune comparisons found"

        false_positives = [
            f"{r.nom_enseigne} falsely contained in {r.foreign_commune}/{r.foreign_zone}"
            for r in rows if r.false_containment is True
        ]
        assert not false_positives, f"Spatial boundary leakage detected: {false_positives}"


# ==============================================================================
# 3. IDEMPOTENCY STRESS TESTS
# ==============================================================================

class TestIdempotencyStress:
    """Verifies that re-running initialization and seed scripts is safe and does not duplicate keys."""

    def test_seed_zones_re_execution_stability(self, db_session):
        """
        Verifies that re-executing seed_zones() does not crash or generate duplicate primary keys.
        """
        # Run seed_zones
        summary = seed_zones(db_session)
        assert summary["zones"] == 9
        assert summary["demographie"] == 9
        assert summary["accessibilite"] == 9
        assert summary["pois"] == 13

        # Verify no duplicate IDs exist in the database for pilot zones
        query = text("""
            SELECT id, count(*)
            FROM zones_geographiques
            WHERE id IN :zone_ids
            GROUP BY id
            HAVING count(*) > 1;
        """)
        dup_zones = db_session.execute(query, {"zone_ids": tuple(PILOT_ZONE_IDS)}).fetchall()
        assert not dup_zones, f"Duplicate zone IDs found: {dup_zones}"

        query_poi = text("""
            SELECT id, count(*)
            FROM infrastructures_commerces
            WHERE id IN :poi_ids
            GROUP BY id
            HAVING count(*) > 1;
        """)
        dup_pois = db_session.execute(query_poi, {"poi_ids": tuple(PILOT_POI_IDS)}).fetchall()
        assert not dup_pois, f"Duplicate POI IDs found: {dup_pois}"

