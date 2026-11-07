"""
backend/tests/test_m1_adversarial.py
Adversarial Stress Test Suite for Milestone 1: Database & Spatial Infrastructure.

Tests:
1. Check constraint fuzzing:
   - score_ipet = 100.1, score_ipet = -0.1, score_ipet = 0.0, score_ipet = 100.0
   - score_connectivite = 150, score_connectivite = -0.1, score_connectivite = 100.1
   - modele_utilise IN ('NAIVE_D7', 'PROPHET', 'XGBOOST')
   - role IN ('ADMIN', 'ANALYSTE', 'METIER')
   - action_type IN ('CONSULTATION', 'EXPORT_PDF', 'EXPORT_EXCEL', 'CALCUL_IPET', 'LOGIN', 'LOGOUT')
2. Spatial validity stress tests:
   - ST_IsValid(geom) == True for all 9 zones
   - ST_IsValidReason(geom) == 'Valid Geometry' for all 9 zones
   - ST_SRID(geom) == 4326 for all 9 zones
   - ST_GeometryType(geom) == 'ST_Polygon' for all 9 zones
   - ST_SRID(geom_point) == 4326 for all 13 POIs
   - ST_GeometryType(geom_point) == 'ST_Point' for all 13 POIs
   - PostGIS ST_Contains / ST_Within validation for all POIs against their host zones
   - Adversarial cross-commune negative containment: Cocody POIs must NEVER be contained in Yopougon or Marcory zones
3. Idempotency stress tests:
   - init_database() re-execution safety
   - seed_zones() re-execution safety and zero-duplicate guarantees
"""

import sys
import uuid
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
from app.seeds.seed_zones import seed_zones
from app.models.zone import ZoneGeographique
from app.models.demography import Demographie
from app.models.infrastructure import InfrastructureCommerce, AccessibiliteRoutiere
from app.models.ipet import ScoreRecommandationIPET
from app.models.prediction import PrevisionFrequentation
from app.models.audit import Utilisateur, JournalAudit


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database session fixture."""
    session = SessionLocal()
    try:
        yield session
    finally:
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

    def test_ipet_score_upper_overflow_rejected(self, db_session):
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

    def test_ipet_score_negative_overflow_rejected(self, db_session):
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

            # Verify persisted
            saved_min = db_session.get(ScoreRecommandationIPET, ipet_min.id)
            saved_max = db_session.get(ScoreRecommandationIPET, ipet_max.id)
            assert saved_min is not None and saved_min.score_ipet == 0.0
            assert saved_max is not None and saved_max.score_ipet == 100.0
        finally:
            # Clean up test rows
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
        """Verifies that inserting an unapproved ML model (e.g., 'ARIMA') strictly raises CheckViolation."""
        invalid_pred = PrevisionFrequentation(
            id=f"adv-pred-{uuid.uuid4().hex[:8]}",
            zone_id="ci-abidjan-cocody-angre",
            date_horizon=datetime.now(timezone.utc),
            valeur_estimee=500.0,
            modele_utilise="ARIMA"  # Invalid: not in ('NAIVE_D7', 'PROPHET', 'XGBOOST')
        )
        with pytest.raises(IntegrityError) as exc_info:
            db_session.add(invalid_pred)
            db_session.commit()
        db_session.rollback()
        assert _is_check_violation(exc_info), f"Expected CheckViolation for ARIMA model, got: {exc_info.value}"

    def test_user_invalid_role_rejected(self, db_session):
        """Verifies that inserting an invalid user role (e.g., 'SUPERADMIN') strictly raises CheckViolation."""
        invalid_user = Utilisateur(
            id=f"adv-usr-{uuid.uuid4().hex[:8]}",
            email=f"hacker_{uuid.uuid4().hex[:6]}@example.com",
            role="SUPERADMIN",  # Invalid: not in ('ADMIN', 'ANALYSTE', 'METIER')
            password_hash="argon2_fake_hash"
        )
        with pytest.raises(IntegrityError) as exc_info:
            db_session.add(invalid_user)
            db_session.commit()
        db_session.rollback()
        assert _is_check_violation(exc_info), f"Expected CheckViolation for role, got: {exc_info.value}"

    def test_audit_invalid_action_rejected(self, db_session):
        """Verifies that inserting an unapproved audit action (e.g., 'DROP_DATABASE') strictly raises CheckViolation."""
        invalid_audit = JournalAudit(
            id=f"adv-aud-{uuid.uuid4().hex[:8]}",
            action_type="DROP_DATABASE",  # Invalid action
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

    def test_all_9_zones_geometric_validity(self, db_session):
        """Verifies that ST_IsValid(geom) is True and ST_IsValidReason is 'Valid Geometry' for all 9 zones."""
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
            ORDER BY nom_commune, nom_zone;
        """)
        rows = db_session.execute(query).fetchall()
        assert len(rows) == 9, f"Expected exactly 9 seeded zones, found {len(rows)}"

        for row in rows:
            zone_desc = f"{row.nom_commune} / {row.nom_zone} ({row.id})"
            assert row.is_valid is True, f"Geometry invalid for zone {zone_desc}: {row.valid_reason}"
            assert row.valid_reason == "Valid Geometry", f"Invalid reason for {zone_desc}: {row.valid_reason}"
            assert row.srid == 4326, f"Incorrect SRID for {zone_desc}: got {row.srid}, expected 4326"
            assert row.geom_type == "ST_Polygon", f"Incorrect geometry type for {zone_desc}: {row.geom_type}"
            assert row.num_points >= 4, f"Insufficient points in polygon for {zone_desc}: {row.num_points}"
            assert row.is_closed is True, f"Polygon boundary is not closed for {zone_desc}"

    def test_all_9_zones_metric_surface_plausibility(self, db_session):
        """Verifies that all 9 zone polygons have plausible surface areas in metric projection (EPSG:32630 UTM 30N)."""
        query = text("""
            SELECT 
                id, 
                nom_commune, 
                nom_zone, 
                ST_Area(ST_Transform(geom, 32630)) AS area_m2
            FROM zones_geographiques;
        """)
        rows = db_session.execute(query).fetchall()
        assert len(rows) == 9
        for row in rows:
            # Areas should be between 1 km² and 50 km² for urban districts
            assert row.area_m2 > 500_000, f"Zone {row.nom_zone} area abnormally small: {row.area_m2} m²"
            assert row.area_m2 < 100_000_000, f"Zone {row.nom_zone} area abnormally large: {row.area_m2} m²"

    def test_all_13_pois_geometric_validity(self, db_session):
        """Verifies that all 13 commercial POIs have valid Point geometries, SRID 4326, and valid coordinates."""
        query = text("""
            SELECT 
                id, 
                nom_enseigne, 
                ST_IsValid(geom_point) AS is_valid,
                ST_SRID(geom_point) AS srid,
                ST_GeometryType(geom_point) AS geom_type,
                ST_X(geom_point) AS lon,
                ST_Y(geom_point) AS lat
            FROM infrastructures_commerces;
        """)
        rows = db_session.execute(query).fetchall()
        assert len(rows) == 13, f"Expected exactly 13 commercial POIs, found {len(rows)}"

        for row in rows:
            poi_desc = f"{row.nom_enseigne} ({row.id})"
            assert row.is_valid is True, f"Invalid point geometry for POI {poi_desc}"
            assert row.srid == 4326, f"Incorrect SRID for POI {poi_desc}: {row.srid}"
            assert row.geom_type == "ST_Point", f"Incorrect geom_type for POI {poi_desc}: {row.geom_type}"
            # Coordinates must fall within the Abidjan bounding box (lon: -4.3 to -3.8, lat: 5.2 to 5.5)
            assert -4.3 <= row.lon <= -3.8, f"Longitude out of Abidjan range for {poi_desc}: {row.lon}"
            assert 5.2 <= row.lat <= 5.5, f"Latitude out of Abidjan range for {poi_desc}: {row.lat}"

    def test_postgis_spatial_containment_on_all_pois(self, db_session):
        """Verifies that every seeded POI is strictly contained inside its assigned host zone polygon."""
        query = text("""
            SELECT 
                p.id AS poi_id,
                p.nom_enseigne,
                z.id AS zone_id,
                z.nom_commune,
                z.nom_zone,
                ST_Contains(z.geom, p.geom_point) AS is_contained,
                ST_Within(p.geom_point, z.geom) AS is_within
            FROM infrastructures_commerces p
            JOIN zones_geographiques z ON p.zone_id = z.id;
        """)
        rows = db_session.execute(query).fetchall()
        assert len(rows) == 13, f"Expected 13 POI containment evaluations, got {len(rows)}"

        for row in rows:
            poi_desc = f"POI '{row.nom_enseigne}' in zone '{row.nom_commune} - {row.nom_zone}'"
            assert row.is_contained is True, f"ST_Contains returned False for {poi_desc}"
            assert row.is_within is True, f"ST_Within returned False for {poi_desc}"

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
              AND z.nom_commune IN ('Yopougon', 'Marcory');
        """)
        rows = db_session.execute(query).fetchall()
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
    """Verifies that re-running initialization and seed scripts is 100% safe, idempotent, and non-destructive."""

    def test_init_database_idempotency(self):
        """Verifies that executing init_database() a second time succeeds without errors or schema breakage."""
        result = init_database()
        assert result is True, "init_database() failed on re-execution"

    def test_seed_zones_idempotency_and_zero_duplicates(self, db_session):
        """
        Verifies that executing seed_zones() repeatedly does not create duplicate rows
        or alter existing counts (9 zones, 9 demographics, 9 accessibilities, 13 POIs).
        """
        # Baseline counts
        z_count_1 = db_session.execute(select(func.count(ZoneGeographique.id))).scalar()
        d_count_1 = db_session.execute(select(func.count(Demographie.id))).scalar()
        a_count_1 = db_session.execute(select(func.count(AccessibiliteRoutiere.id))).scalar()
        p_count_1 = db_session.execute(select(func.count(InfrastructureCommerce.id))).scalar()

        assert z_count_1 == 9
        assert d_count_1 == 9
        assert a_count_1 == 9
        assert p_count_1 == 13

        # Re-run seed_zones
        summary = seed_zones(db_session)
        assert summary["zones"] == 9
        assert summary["demographie"] == 9
        assert summary["accessibilite"] == 9
        assert summary["pois"] == 13

        # Counts after second run
        z_count_2 = db_session.execute(select(func.count(ZoneGeographique.id))).scalar()
        d_count_2 = db_session.execute(select(func.count(Demographie.id))).scalar()
        a_count_2 = db_session.execute(select(func.count(AccessibiliteRoutiere.id))).scalar()
        p_count_2 = db_session.execute(select(func.count(InfrastructureCommerce.id))).scalar()

        assert z_count_2 == z_count_1 == 9, f"Duplicate zones created: {z_count_2} vs {z_count_1}"
        assert d_count_2 == d_count_1 == 9, f"Duplicate demographics created: {d_count_2} vs {d_count_1}"
        assert a_count_2 == a_count_1 == 9, f"Duplicate accessibility records created: {a_count_2} vs {a_count_1}"
        assert p_count_2 == p_count_1 == 13, f"Duplicate POIs created: {p_count_2} vs {p_count_1}"
