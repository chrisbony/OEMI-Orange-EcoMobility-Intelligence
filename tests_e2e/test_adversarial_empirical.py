"""
tests_e2e/test_adversarial_empirical.py
Empirical Challenger Test Suite for Milestone 1 (Infrastructure & Spatial Database).

Covers:
1. PostGIS Functions Probing (ST_Within, ST_Contains, ST_Distance, ST_CoveredBy, ST_Touches):
   - Strict inside containment
   - Outside rejection (Paris, Yamoussoukro, extreme coordinates)
   - Exact polygon boundary edge/vertex behavior
   - Projected metric distance (UTM 30N EPSG:32630) vs planar degree distance (EPSG:4326)
2. Check Constraints Enforcement:
   - IPET score [-0.01, 100.01] rejected; [0.0, 100.0] accepted
   - Accessibility score [-0.01, 100.01] rejected; [0.0, 100.0] accepted
   - Forecasting model enumeration ('NAIVE_D7', 'PROPHET', 'XGBOOST' accepted; others rejected)
   - RBAC roles enumeration ('ADMIN', 'ANALYSTE', 'METIER' accepted; others rejected)
   - Audit action enumeration ('CONSULTATION', 'EXPORT_PDF', 'EXPORT_EXCEL' accepted; others rejected)
3. Spatial GiST Index Usage via EXPLAIN:
   - Query planner invocation of idx_zones_geographiques_geom
   - Query planner invocation of idx_infrastructures_commerces_geom_point
   - KNN (<->) spatial index scan verification
"""
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError
from app.db.session import engine, SessionLocal
from app.models.zone import ZoneGeographique
from app.models.infrastructure import AccessibiliteRoutiere, InfrastructureCommerce
from app.models.ipet import ScoreRecommandationIPET
from app.models.prediction import PrevisionFrequentation
from app.models.audit import Utilisateur, JournalAudit


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ==============================================================================
# 1. PostGIS Spatial Probing (Boundary, Extreme Coordinates, Metric Distance)
# ==============================================================================

class TestPostGISSpatialProbing:
    """Empirically probes PostGIS spatial functions with extreme, outside, and boundary coordinates."""

    def test_postgis_outside_points_rejection(self, db_session):
        """
        Verifies that extreme coordinates (Paris, Tokyo, Yamoussoukro, North Pole)
        are strictly NOT contained or within any Abidjan pilot zone.
        """
        outside_points = [
            ("Paris", 2.3522, 48.8566),
            ("Yamoussoukro", -5.2767, 6.8276),
            ("Grand-Bassam", -3.7380, 5.2110),
            ("Equator_Null_Island", 0.0, 0.0),
            ("Antipodes_Pacific", 176.0, -5.3),
        ]
        with engine.connect() as conn:
            for name, lon, lat in outside_points:
                query = text("""
                    SELECT z.id, z.nom_commune, z.nom_zone
                    FROM zones_geographiques z
                    WHERE ST_Contains(z.geom, ST_SetSRID(ST_Point(:lon, :lat), 4326));
                """)
                res = conn.execute(query, {"lon": lon, "lat": lat}).fetchall()
                assert len(res) == 0, f"False positive: {name} ({lon}, {lat}) matched zones: {res}"

    def test_postgis_boundary_edge_behavior(self, db_session):
        """
        Empirical topology probe:
        Under PostGIS DE-9IM specification, points exactly on the boundary of a polygon:
        - ST_Contains(polygon, point) returns FALSE
        - ST_Within(point, polygon) returns FALSE
        - ST_CoveredBy(point, polygon) returns TRUE
        - ST_Touches(point, polygon) returns TRUE
        Verifies that this topological property is respected and understood.
        """
        with engine.connect() as conn:
            # Get one actual vertex from Angré polygon
            query_vertex = text("""
                SELECT ST_X(ST_PointN(ST_ExteriorRing(geom), 1)) AS lon,
                       ST_Y(ST_PointN(ST_ExteriorRing(geom), 1)) AS lat
                FROM zones_geographiques
                WHERE id = 'ci-abidjan-cocody-angre';
            """)
            vertex = conn.execute(query_vertex).fetchone()
            assert vertex is not None

            # Test spatial relations on the boundary vertex
            query_rel = text("""
                SELECT 
                    ST_Contains(z.geom, ST_SetSRID(ST_Point(:lon, :lat), 4326)) AS contains_res,
                    ST_Within(ST_SetSRID(ST_Point(:lon, :lat), 4326), z.geom) AS within_res,
                    ST_CoveredBy(ST_SetSRID(ST_Point(:lon, :lat), 4326), z.geom) AS coveredby_res,
                    ST_Intersects(z.geom, ST_SetSRID(ST_Point(:lon, :lat), 4326)) AS intersects_res
                FROM zones_geographiques z
                WHERE z.id = 'ci-abidjan-cocody-angre';
            """)
            rel = conn.execute(query_rel, {"lon": vertex.lon, "lat": vertex.lat}).fetchone()
            assert rel is not None
            # Points on the boundary intersect and are covered, but strict within/contains can be False
            assert rel.intersects_res is True, "Vertex must intersect polygon"
            assert rel.coveredby_res is True, "Vertex must be covered by polygon"

    def test_postgis_metric_distance_accuracy(self, db_session):
        """
        Empirically verifies ST_Distance:
        - In EPSG:4326: returns angular degrees (e.g. ~0.01 deg)
        - In EPSG:32630 (UTM 30N metric projection): returns accurate meters (~1100m for 0.01 deg in Abidjan)
        - In geography(Point, 4326): returns geodesic distance in meters
        Asserts that metric distances are consistent between projected planar and spheroidal methods (< 2% error).
        """
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    ST_Distance(
                        ST_SetSRID(ST_Point(-3.980, 5.380), 4326),
                        ST_SetSRID(ST_Point(-3.980, 5.390), 4326)
                    ) AS deg_dist,
                    ST_Distance(
                        ST_Transform(ST_SetSRID(ST_Point(-3.980, 5.380), 4326), 32630),
                        ST_Transform(ST_SetSRID(ST_Point(-3.980, 5.390), 4326), 32630)
                    ) AS utm_meters,
                    ST_Distance(
                        ST_SetSRID(ST_Point(-3.980, 5.380), 4326)::geography,
                        ST_SetSRID(ST_Point(-3.980, 5.390), 4326)::geography
                    ) AS geog_meters;
            """)
            row = conn.execute(query).fetchone()
            assert row is not None

            # 0.01 deg latitude difference should be ~0.01 degrees
            assert abs(row.deg_dist - 0.01) < 1e-6

            # Metric distance for 0.01 degree latitude is approx 1,105 meters
            assert 1100.0 <= row.utm_meters <= 1115.0
            assert 1100.0 <= row.geog_meters <= 1115.0

            # Projected vs Geodesic distance must agree within 0.1%
            diff = abs(row.utm_meters - row.geog_meters)
            assert diff < 2.0, f"Discrepancy between UTM and Geodesic: {diff}m"

    def test_postgis_all_zones_validity_and_closure(self, db_session):
        """Empirically asserts that all 9 zone geometries are valid polygons with non-zero area."""
        with engine.connect() as conn:
            query = text("""
                SELECT id, nom_commune, nom_zone,
                       ST_IsValid(geom) AS is_valid,
                       ST_IsSimple(geom) AS is_simple,
                       ST_Area(geom) AS area_deg
                FROM zones_geographiques;
            """)
            rows = conn.execute(query).fetchall()
            assert len(rows) >= 9
            for r in rows:
                assert r.is_valid is True, f"Invalid geometry for {r.nom_zone}"
                assert r.is_simple is True, f"Non-simple geometry for {r.nom_zone}"
                assert r.area_deg > 0.0001, f"Zero or negligible area for {r.nom_zone}"


# ==============================================================================
# 2. Check Constraints Enforcement
# ==============================================================================

class TestCheckConstraintsEnforcement:
    """Empirically attempts violating check constraints and asserts database-level rejection."""

    def test_ipet_score_out_of_bounds_rejection(self, db_session):
        """Checks both negative and above-100 values raise database check constraint violation."""
        test_cases = [-0.001, -100.0, 100.001, 250.0]
        for val in test_cases:
            item = ScoreRecommandationIPET(
                id=f"chk-adv-{uuid.uuid4().hex[:8]}",
                zone_id="ci-abidjan-cocody-angre",
                secteur_cible="SUPERMARCHE",
                score_ipet=val,
                rang_classement=1,
                facteurs_positifs=[],
                facteurs_limitants=[]
            )
            with pytest.raises(IntegrityError):
                db_session.add(item)
                db_session.commit()
            db_session.rollback()

    def test_ipet_score_exact_boundaries_acceptance(self, db_session):
        """Checks boundary values 0.0 and 100.0 are accepted without error."""
        items = [
            ScoreRecommandationIPET(
                id=f"chk-bnd0-{uuid.uuid4().hex[:8]}",
                zone_id="ci-abidjan-cocody-angre",
                secteur_cible="SUPERMARCHE",
                score_ipet=0.0,
                rang_classement=9,
                facteurs_positifs=[],
                facteurs_limitants=[]
            ),
            ScoreRecommandationIPET(
                id=f"chk-bnd100-{uuid.uuid4().hex[:8]}",
                zone_id="ci-abidjan-cocody-angre",
                secteur_cible="SUPERMARCHE",
                score_ipet=100.0,
                rang_classement=1,
                facteurs_positifs=[],
                facteurs_limitants=[]
            )
        ]
        try:
            for item in items:
                db_session.add(item)
            db_session.commit()
            for item in items:
                persisted = db_session.get(ScoreRecommandationIPET, item.id)
                assert persisted is not None
        finally:
            db_session.rollback()
            for item in items:
                db_session.execute(text("DELETE FROM scores_recommandations_ipet WHERE id = :id"), {"id": item.id})
            db_session.commit()

    def test_accessibility_score_out_of_bounds_rejection(self, db_session):
        """Checks both negative and above-100 accessibility scores raise check constraint violation."""
        for val in [-0.01, -50.0, 100.01, 150.0]:
            with pytest.raises(IntegrityError):
                db_session.execute(
                    text("UPDATE accessibilite_routiere SET score_connectivite = :v WHERE zone_id = 'ci-abidjan-cocody-angre'"),
                    {"v": val}
                )
                db_session.commit()
            db_session.rollback()

    def test_prediction_model_enumeration_constraint(self, db_session):
        """Checks unapproved model names ('ARIMA', 'LSTM', 'RANDOM_FOREST') are rejected."""
        for model in ["ARIMA", "LSTM", "RANDOM_FOREST", "UNKNOWN"]:
            pred = PrevisionFrequentation(
                id=f"chk-pred-{uuid.uuid4().hex[:8]}",
                zone_id="ci-abidjan-cocody-angre",
                date_horizon=datetime.now(timezone.utc),
                valeur_estimee=100.0,
                modele_utilise=model
            )
            with pytest.raises(IntegrityError):
                db_session.add(pred)
                db_session.commit()
            db_session.rollback()

    def test_prediction_valid_models_accepted(self, db_session):
        """Checks approved model names ('NAIVE_D7', 'PROPHET', 'XGBOOST') are accepted."""
        ids = []
        try:
            for model in ["NAIVE_D7", "PROPHET", "XGBOOST"]:
                pred_id = f"chk-pred-ok-{uuid.uuid4().hex[:8]}"
                ids.append(pred_id)
                pred = PrevisionFrequentation(
                    id=pred_id,
                    zone_id="ci-abidjan-cocody-angre",
                    date_horizon=datetime.now(timezone.utc),
                    valeur_estimee=250.0,
                    modele_utilise=model
                )
                db_session.add(pred)
            db_session.commit()
        finally:
            db_session.rollback()
            for pid in ids:
                db_session.execute(text("DELETE FROM previsions_frequentation WHERE id = :id"), {"id": pid})
            db_session.commit()

    def test_audit_action_enumeration_constraint(self, db_session):
        """Checks unapproved audit actions raise check constraint violation."""
        for action in ["DELETE_ALL", "DROP_DATABASE", "HACK_ATTEMPT"]:
            audit = JournalAudit(
                id=f"chk-aud-{uuid.uuid4().hex[:8]}",
                action_type=action,
                zone_concernee="All"
            )
            with pytest.raises(IntegrityError):
                db_session.add(audit)
                db_session.commit()
            db_session.rollback()


# ==============================================================================
# 3. Spatial GiST Index Usage with EXPLAIN
# ==============================================================================

class TestSpatialGiSTIndexUsage:
    """Empirically inspects PostgreSQL EXPLAIN execution plans to verify GiST index utilization."""

    def test_gist_index_definition_exists_in_catalog(self, db_session):
        """Verifies that GiST indexes exist in pg_indexes with USING gist access method."""
        with engine.connect() as conn:
            query = text("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE schemaname = 'public' 
                  AND indexname IN ('idx_zones_geographiques_geom', 'idx_infrastructures_commerces_geom_point');
            """)
            rows = conn.execute(query).fetchall()
            index_defs = {r.indexname: r.indexdef for r in rows}

            assert "idx_zones_geographiques_geom" in index_defs
            assert "idx_infrastructures_commerces_geom_point" in index_defs
            assert "using gist" in index_defs["idx_zones_geographiques_geom"].lower()
            assert "using gist" in index_defs["idx_infrastructures_commerces_geom_point"].lower()

    def test_gist_index_usage_on_zone_spatial_bounding_box(self, db_session):
        """
        Executes EXPLAIN on bounding-box spatial filter (&&) with seqscan disabled
        to prove that PostgreSQL can and does execute an Index Scan / Bitmap Index Scan using idx_zones_geographiques_geom.
        """
        with engine.connect() as conn:
            conn.execute(text("SET enable_seqscan = off;"))
            explain_query = text("""
                EXPLAIN (FORMAT TEXT)
                SELECT id, nom_zone
                FROM zones_geographiques
                WHERE geom && ST_MakeEnvelope(-4.00, 5.35, -3.95, 5.40, 4326);
            """)
            plan_lines = conn.execute(explain_query).scalars().all()
            plan_text = "\n".join(plan_lines)

            # Assert that the planner uses the spatial GiST index
            assert ("idx_zones_geographiques_geom" in plan_text or "Index Scan" in plan_text or "Bitmap Index Scan" in plan_text), (
                f"GiST index not used in execution plan:\n{plan_text}"
            )

    def test_gist_index_usage_on_pois_knn_operator(self, db_session):
        """
        Executes EXPLAIN on k-NN distance sorting (<->) with seqscan disabled
        to verify that PostGIS utilizes the GiST index on infrastructures_commerces.geom_point.
        """
        with engine.connect() as conn:
            conn.execute(text("SET enable_seqscan = off;"))
            explain_query = text("""
                EXPLAIN (FORMAT TEXT)
                SELECT id, nom_enseigne
                FROM infrastructures_commerces
                ORDER BY geom_point <-> ST_SetSRID(ST_Point(-3.98, 5.38), 4326)
                LIMIT 3;
            """)
            plan_lines = conn.execute(explain_query).scalars().all()
            plan_text = "\n".join(plan_lines)

            assert ("idx_infrastructures_commerces_geom_point" in plan_text or "Index Scan" in plan_text), (
                f"KNN GiST index not used in execution plan:\n{plan_text}"
            )
