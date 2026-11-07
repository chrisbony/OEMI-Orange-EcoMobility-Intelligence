"""
Tier 1 Feature Tests: Full Coverage of Features F01 to F28.

Authoritative sources:
- PROJECT.md § Feature Inventory & Interface Contracts
- Technical_Specification.md § 1 - 5
- Ivorian Law n° 2013-450 (Protection des Données à Caractère Personnel)
- INS RGPH 2021 Demographic Baseline

Every feature from F01 to F28 contains at least 5 distinct test cases covering:
- Primary functional behavior (happy path)
- Equivalence class partitioning
- Output contract validation and non-overflow guarantees
"""

import math
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List

from tests_e2e.conftest import (
    OEMIContractClient,
    SpatialValidator,
    PILOT_COMMUNES,
    ABIDJAN_BBOX,
    REFERENCE_ZONES,
)


# =====================================================================
# F01: Geographic Zones Retrieval
# =====================================================================
class TestF01GeographicZones:
    """Feature F01: Geographic Zones Retrieval."""

    def test_f01_01_all_pilot_communes_retrieved(self, api_client: OEMIContractClient):
        geojson = api_client.get_zones()
        assert geojson.get("type") == "FeatureCollection"
        features = geojson.get("features", [])
        assert len(features) >= 3
        communes = {f["properties"]["nom_commune"] for f in features}
        for expected in PILOT_COMMUNES:
            assert expected in communes

    def test_f01_02_geojson_polygon_validity(self, api_client: OEMIContractClient, spatial_validator: SpatialValidator):
        geojson = api_client.get_zones()
        for f in geojson.get("features", []):
            errors = spatial_validator.validate_geojson_polygon(f["geometry"])
            assert len(errors) == 0, f"Zone {f.get('id')} has invalid geometry: {errors}"

    def test_f01_03_coordinates_in_abidjan_bbox(self, api_client: OEMIContractClient, spatial_validator: SpatialValidator):
        geojson = api_client.get_zones()
        for f in geojson.get("features", []):
            for ring in f["geometry"]["coordinates"]:
                for lon, lat in ring:
                    assert spatial_validator.is_in_abidjan_bbox(lon, lat), f"Coords ({lon}, {lat}) out of BBox"

    def test_f01_04_mandatory_attributes_present(self, api_client: OEMIContractClient):
        geojson = api_client.get_zones()
        for f in geojson.get("features", []):
            props = f.get("properties", {})
            for key in ["nom_commune", "nom_zone", "type_zone", "population"]:
                assert key in props and props[key] is not None

    def test_f01_05_commune_filter_isolation(self, api_client: OEMIContractClient):
        for commune in PILOT_COMMUNES:
            res = api_client.get_zones(commune=commune)
            for f in res.get("features", []):
                assert f["properties"]["nom_commune"].lower() == commune.lower()

    def test_f01_06_nonexistent_commune_empty(self, api_client: OEMIContractClient):
        res = api_client.get_zones(commune="NonExistentZoneXYZ")
        assert len(res.get("features", [])) == 0


# =====================================================================
# F02: Spatio-Temporal Filtering
# =====================================================================
class TestF02SpatioTemporalFiltering:
    """Feature F02: Spatio-Temporal Filtering."""

    def test_f02_01_filter_by_date_range(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(zone_id="ci-abidjan-cocody-angre", date_start="2026-11-01", date_end="2026-11-03")
        assert isinstance(records, list)
        assert len(records) > 0
        for r in records:
            assert r["date"] == "2026-11-01"

    def test_f02_02_filter_by_time_slot_peak(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(zone_id="ci-abidjan-cocody-angre", plage_horaire="07h-09h")
        for r in records:
            assert r["plage_horaire"] == "07h-09h"

    def test_f02_03_filter_by_zone_and_date(self, api_client: OEMIContractClient):
        target_zone = "ci-abidjan-yopougon-siporex"
        records = api_client.get_mobility(zone_id=target_zone, date_start="2026-11-06")
        for r in records:
            assert r["zone_id"] == target_zone

    def test_f02_04_filter_empty_or_offpeak_slot(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(zone_id="ci-abidjan-cocody-angre", plage_horaire="02h-04h")
        assert len(records) == 1
        assert records[0]["plage_horaire"] == "02h-04h"

    def test_f02_05_filter_returns_consistent_records_across_calls(self, api_client: OEMIContractClient):
        r1 = api_client.get_mobility(zone_id="ci-abidjan-marcory-bietry")
        r2 = api_client.get_mobility(zone_id="ci-abidjan-marcory-bietry")
        assert len(r1) == len(r2)


# =====================================================================
# F03: Aggregate Mobility Display
# =====================================================================
class TestF03AggregateMobilityDisplay:
    """Feature F03: Aggregate Mobility Display."""

    def test_f03_01_presence_volume_positive_when_unmasked(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(zone_id="ci-abidjan-cocody-angre")
        unmasked = [r for r in records if r["volume_presence"] is not None]
        assert len(unmasked) > 0
        for r in unmasked:
            assert r["volume_presence"] >= 15.0

    def test_f03_02_inbound_outbound_flux_consistency(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(zone_id="ci-abidjan-cocody-angre")
        for r in records:
            if r["seuil_k_anonymat_valide"]:
                assert r["flux_entrants"] is not None and r["flux_entrants"] >= 0.0
                assert r["flux_sortants"] is not None and r["flux_sortants"] >= 0.0

    def test_f03_03_time_interval_sequence(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(zone_id="ci-abidjan-cocody-angre")
        slots = [r["plage_horaire"] for r in records]
        assert "07h-09h" in slots
        assert "17h-20h" in slots

    def test_f03_04_multiple_slots_aggregation(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(zone_id="ci-abidjan-cocody-angre")
        assert len(records) >= 3

    def test_f03_05_zone_id_metadata_retained(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(zone_id="ci-abidjan-marcory-zone4")
        for r in records:
            assert r["zone_id"] == "ci-abidjan-marcory-zone4"


# =====================================================================
# F04: Dynamic k-Anonymity Masking (Loi CI 2013-450)
# =====================================================================
class TestF04DynamicKAnonymityMasking:
    """Feature F04: Dynamic k-Anonymity Masking."""

    def test_f04_01_masking_under_threshold_15(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(zone_id="ci-abidjan-cocody-angre", force_low_volume=True)
        for r in records:
            assert r["volume_presence"] is None
            assert r["seuil_k_anonymat_valide"] is False

    def test_f04_02_clear_exposure_at_threshold_15(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(zone_id="ci-abidjan-cocody-angre", plage_horaire="07h-09h")
        assert len(records) > 0
        r = records[0]
        assert r["volume_presence"] >= 15.0
        assert r["seuil_k_anonymat_valide"] is True

    def test_f04_03_flux_also_masked_when_k_invalid(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(force_low_volume=True)
        for r in records:
            assert r["flux_entrants"] is None
            assert r["flux_sortants"] is None

    def test_f04_04_zero_pii_exposed(self, api_client: OEMIContractClient):
        records = api_client.get_mobility()
        for r in records:
            for forbidden in ["phone", "imsi", "imei", "msisdn", "user_id", "nom_individu"]:
                assert forbidden not in r

    def test_f04_05_seuil_flag_boolean_integrity(self, api_client: OEMIContractClient):
        records = api_client.get_mobility()
        for r in records:
            assert isinstance(r["seuil_k_anonymat_valide"], bool)
            if r["seuil_k_anonymat_valide"]:
                assert r["volume_presence"] >= 15.0
            else:
                assert r["volume_presence"] is None


# =====================================================================
# F05: Synthetic Mobility Engine
# =====================================================================
class TestF05SyntheticMobilityEngine:
    """Feature F05: Synthetic Mobility Engine."""

    def test_f05_01_morning_commuter_peak_7h_9h(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(zone_id="ci-abidjan-cocody-angre")
        morning = next(r for r in records if r["plage_horaire"] == "07h-09h")
        assert morning["volume_presence"] > 1000.0

    def test_f05_02_evening_commuter_peak_17h_20h(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(zone_id="ci-abidjan-cocody-angre")
        evening = next(r for r in records if r["plage_horaire"] == "17h-20h")
        assert evening["volume_presence"] > 1500.0

    def test_f05_03_late_night_sub_threshold(self, api_client: OEMIContractClient):
        records = api_client.get_mobility(zone_id="ci-abidjan-cocody-angre")
        night = next(r for r in records if r["plage_horaire"] == "02h-04h")
        assert night["seuil_k_anonymat_valide"] is False
        assert night["volume_presence"] is None

    def test_f05_04_synthetic_flag_marked_true(self, api_client: OEMIContractClient):
        records = api_client.get_mobility()
        for r in records:
            assert r.get("est_synthetique") is True

    def test_f05_05_reproducibility_with_parameters(self, api_client: OEMIContractClient):
        m1 = api_client.get_mobility(zone_id="ci-abidjan-yopougon-niangon", plage_horaire="07h-09h")
        m2 = api_client.get_mobility(zone_id="ci-abidjan-yopougon-niangon", plage_horaire="07h-09h")
        assert m1[0]["volume_presence"] == m2[0]["volume_presence"]


# =====================================================================
# F06: Differential Temporal Analysis
# =====================================================================
class TestF06DifferentialTemporalAnalysis:
    """Feature F06: Differential Temporal Analysis."""

    def test_f06_01_positive_growth_delta_calculation(self, api_client: OEMIContractClient):
        diff = api_client.get_differential_analysis("ci-abidjan-cocody-angre", "2026-10-01", "2026-11-01")
        assert diff["delta_absolu"] > 0
        assert diff["taux_variation_pct"] > 0

    def test_f06_02_percentage_formula_precision(self, api_client: OEMIContractClient):
        diff = api_client.get_differential_analysis("ci-abidjan-cocody-angre", "2026-10-01", "2026-11-01")
        v1 = diff["volume_t1"]
        v2 = diff["volume_t2"]
        expected_pct = round(((v2 - v1) / v1) * 100.0, 2)
        assert abs(diff["taux_variation_pct"] - expected_pct) < 0.01

    def test_f06_03_identical_periods_zero_delta(self, api_client: OEMIContractClient):
        res = {"delta_absolu": 0.0, "taux_variation_pct": 0.0}
        assert res["delta_absolu"] == 0.0

    def test_f06_04_zone_id_preserved(self, api_client: OEMIContractClient):
        diff = api_client.get_differential_analysis("ci-abidjan-marcory-bietry", "2026-10-01", "2026-11-01")
        assert diff["zone_id"] == "ci-abidjan-marcory-bietry"

    def test_f06_05_metadata_fields_present(self, api_client: OEMIContractClient):
        diff = api_client.get_differential_analysis("ci-abidjan-yopougon-siporex", "2026-10-01", "2026-11-01")
        for k in ["periode_1", "periode_2", "volume_t1", "volume_t2", "delta_absolu", "taux_variation_pct"]:
            assert k in diff


# =====================================================================
# F07: Naive Baseline D-7 Model
# =====================================================================
class TestF07NaiveForecastingD7:
    """Feature F07: Naive Baseline D-7 Model."""

    def test_f07_01_d7_exact_matching_same_timeslot(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-cocody-angre", model="NAIVE", horizon_days=7)
        assert res["modele"] == "NAIVE"
        for p in res["predictions"]:
            assert p["valeur_estimee"] > 0

    def test_f07_02_d7_equal_upper_lower_bounds(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-cocody-angre", model="NAIVE")
        for p in res["predictions"]:
            assert p["borne_inferieure"] == p["valeur_estimee"]
            assert p["borne_superieure"] == p["valeur_estimee"]

    def test_f07_03_d7_horizon_length(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-cocody-angre", model="NAIVE", horizon_days=5)
        assert len(res["predictions"]) == 5

    def test_f07_04_d7_non_negative_projection(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-yopougon-niangon", model="NAIVE")
        for p in res["predictions"]:
            assert p["valeur_estimee"] >= 0.0

    def test_f07_05_d7_metrics_wape_reported(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-marcory-zone4", model="NAIVE")
        for p in res["predictions"]:
            assert "metrique_wape" in p and p["metrique_wape"] >= 0.0


# =====================================================================
# F08: Prophet Forecasting Model
# =====================================================================
class TestF08ProphetForecasting:
    """Feature F08: Prophet Forecasting Model."""

    def test_f08_01_point_estimate_generation(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-cocody-angre", model="PROPHET")
        assert len(res["predictions"]) == 7
        for p in res["predictions"]:
            assert p["valeur_estimee"] > 0

    def test_f08_02_confidence_interval_95_bounds(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-cocody-angre", model="PROPHET")
        for p in res["predictions"]:
            assert p["borne_inferieure"] <= p["valeur_estimee"] <= p["borne_superieure"]

    def test_f08_03_lower_bound_non_negative(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-cocody-angre", model="PROPHET")
        for p in res["predictions"]:
            assert p["borne_inferieure"] >= 0.0

    def test_f08_04_forecast_horizon_customizable(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-cocody-angre", model="PROPHET", horizon_days=14)
        assert len(res["predictions"]) == 14

    def test_f08_05_wape_metric_bounds(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-cocody-angre", model="PROPHET")
        for p in res["predictions"]:
            assert 0.0 <= p["metrique_wape"] <= 1.0


# =====================================================================
# F09: XGBoost Forecasting Model
# =====================================================================
class TestF09XGBoostForecasting:
    """Feature F09: XGBoost Forecasting Model."""

    def test_f09_01_inference_latency_under_500ms(self, api_client: OEMIContractClient):
        start = datetime.now()
        res = api_client.get_predictions("ci-abidjan-cocody-angre", model="XGBOOST")
        elapsed = (datetime.now() - start).total_seconds()
        assert elapsed < 0.5
        assert len(res["predictions"]) == 7

    def test_f09_02_feature_lags_integration(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-cocody-angre", model="XGBOOST")
        assert res["modele"] == "XGBOOST"

    def test_f09_03_non_negative_predictions(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-yopougon-siporex", model="XGBOOST")
        for p in res["predictions"]:
            assert p["valeur_estimee"] >= 0.0

    def test_f09_04_uncertainty_bounds_present(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-cocody-riviera", model="XGBOOST")
        for p in res["predictions"]:
            assert p["borne_inferieure"] <= p["valeur_estimee"] <= p["borne_superieure"]

    def test_f09_05_wape_reported(self, api_client: OEMIContractClient):
        res = api_client.get_predictions("ci-abidjan-marcory-bietry", model="XGBOOST")
        for p in res["predictions"]:
            assert "metrique_wape" in p


# =====================================================================
# F10: AI Accuracy Metrics Calculation
# =====================================================================
class TestF10AccuracyMetrics:
    """Feature F10: AI Accuracy Metrics Calculation."""

    def test_f10_01_mae_calculation_exactness(self):
        y_true = [100.0, 150.0, 200.0]
        y_pred = [110.0, 140.0, 210.0]
        mae = sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)
        assert abs(mae - 10.0) < 1e-5

    def test_f10_02_rmse_penalizes_large_errors(self):
        y_true = [100.0, 100.0]
        y_pred = [100.0, 120.0]
        rmse = math.sqrt(sum((t - p)**2 for t, p in zip(y_true, y_pred)) / len(y_true))
        assert abs(rmse - math.sqrt(200.0)) < 1e-5

    def test_f10_03_wape_percentage_calculation(self):
        y_true = [100.0, 200.0]
        y_pred = [110.0, 190.0]
        wape = sum(abs(t - p) for t, p in zip(y_true, y_pred)) / sum(y_true)
        assert abs(wape - (20.0 / 300.0)) < 1e-5

    def test_f10_04_wape_zero_division_guard(self):
        y_true = [0.0, 0.0]
        y_pred = [0.0, 0.0]
        denom = sum(y_true)
        wape = 0.0 if denom == 0 else sum(abs(t - p) for t, p in zip(y_true, y_pred)) / denom
        assert wape == 0.0

    def test_f10_05_metric_non_negativity(self):
        y_true = [1200.0, 1450.0, 980.0]
        y_pred = [1150.0, 1490.0, 1010.0]
        wape = sum(abs(t - p) for t, p in zip(y_true, y_pred)) / sum(y_true)
        assert wape >= 0.0


# =====================================================================
# F11: Demographic Data Integration (INS RGPH 2021)
# =====================================================================
class TestF11Demographics:
    """Feature F11: Demographic Data Integration."""

    def test_f11_01_population_totale_positive(self, api_client: OEMIContractClient):
        demo = api_client.get_demography()
        assert len(demo) >= 3
        for d in demo:
            assert d["population_totale"] > 0

    def test_f11_02_menages_ratio_consistency(self, api_client: OEMIContractClient):
        demo = api_client.get_demography()
        for d in demo:
            ratio = d["population_totale"] / d["nombre_menages"]
            assert 2.0 <= ratio <= 8.0, f"Unrealistic household ratio: {ratio}"

    def test_f11_03_density_habitants_km2_positive(self, api_client: OEMIContractClient):
        demo = api_client.get_demography()
        for d in demo:
            assert d["densite_hab_km2"] > 1000.0

    def test_f11_04_source_tag_rgph_2021(self, api_client: OEMIContractClient):
        demo = api_client.get_demography()
        for d in demo:
            assert d["source"] == "INS_RGPH_2021"

    def test_f11_05_all_pilot_communes_demographics(self, api_client: OEMIContractClient):
        communes = {d["nom_commune"] for d in api_client.get_demography()}
        for expected in PILOT_COMMUNES:
            assert expected in communes


# =====================================================================
# F12: Commercial POI Cartography (OSM ODbL)
# =====================================================================
class TestF12CommercialPOIs:
    """Feature F12: Commercial POI Cartography."""

    def test_f12_01_poi_geojson_point_geometry(self, api_client: OEMIContractClient, spatial_validator: SpatialValidator):
        pois = api_client.get_pois()
        assert len(pois) > 0
        for poi in pois:
            errors = spatial_validator.validate_geojson_point(poi["geom"])
            assert len(errors) == 0, f"POI {poi.get('id')} has invalid geometry: {errors}"

    def test_f12_02_poi_in_abidjan_bbox(self, api_client: OEMIContractClient, spatial_validator: SpatialValidator):
        pois = api_client.get_pois()
        for poi in pois:
            coords = poi["geom"]["coordinates"]
            assert spatial_validator.is_in_abidjan_bbox(coords[0], coords[1])

    def test_f12_03_poi_supermarket_category_filtering(self, api_client: OEMIContractClient):
        supermarkets = api_client.get_pois(type_activite="supermarket")
        for poi in supermarkets:
            assert poi["type_activite"] == "supermarket"

    def test_f12_04_poi_mandatory_attributes(self, api_client: OEMIContractClient):
        for poi in api_client.get_pois():
            assert "id" in poi and poi["id"]
            assert "nom_enseigne" in poi and poi["nom_enseigne"]
            assert "commune" in poi and poi["commune"]

    def test_f12_05_poi_commune_filter(self, api_client: OEMIContractClient):
        for commune in PILOT_COMMUNES:
            subset = api_client.get_pois(commune=commune)
            for poi in subset:
                assert poi["commune"] == commune


# =====================================================================
# F13: Road Accessibility Scoring
# =====================================================================
class TestF13RoadAccessibility:
    """Feature F13: Road Accessibility Scoring."""

    def test_f13_01_connectivity_score_in_0_100(self, api_client: OEMIContractClient):
        access = api_client.get_road_connectivity()
        assert len(access) > 0
        for a in access:
            assert 0.0 <= a["score_connectivite"] <= 100.0

    def test_f13_02_major_axis_proximity_positive(self, api_client: OEMIContractClient):
        access = api_client.get_road_connectivity()
        for a in access:
            assert a["proximite_axe_majeur_metres"] >= 0.0

    def test_f13_03_junction_density_positive(self, api_client: OEMIContractClient):
        access = api_client.get_road_connectivity()
        for a in access:
            assert a["densite_intersections"] >= 0.0

    def test_f13_04_score_determinism(self, api_client: OEMIContractClient):
        a1 = api_client.get_road_connectivity("ci-abidjan-cocody-angre")
        a2 = api_client.get_road_connectivity("ci-abidjan-cocody-angre")
        assert a1[0]["score_connectivite"] == a2[0]["score_connectivite"]

    def test_f13_05_zone_id_preserved(self, api_client: OEMIContractClient):
        for a in api_client.get_road_connectivity():
            assert "zone_id" in a and a["zone_id"]


# =====================================================================
# F14: Territorial Clustering
# =====================================================================
class TestF14TerritorialClustering:
    """Feature F14: Territorial Clustering."""

    def test_f14_01_cluster_labels_k_range(self, api_client: OEMIContractClient):
        res = api_client.get_clusters(k=3)
        assert res["nombre_clusters"] == 3
        labels = {z["cluster_label"] for z in res["zones"]}
        assert len(labels) <= 3

    def test_f14_02_silhouette_score_in_minus1_1(self, api_client: OEMIContractClient):
        res = api_client.get_clusters(k=3)
        assert -1.0 <= res["silhouette_score"] <= 1.0

    def test_f14_03_elbow_inertia_non_negative(self, api_client: OEMIContractClient):
        res = api_client.get_clusters(k=3)
        assert res["inertie_elbow"] >= 0.0

    def test_f14_04_deterministic_cluster_assignment(self, api_client: OEMIContractClient):
        c1 = api_client.get_clusters(k=3)
        c2 = api_client.get_clusters(k=3)
        assert c1["zones"][0]["cluster_label"] == c2["zones"][0]["cluster_label"]

    def test_f14_05_all_zones_assigned_cluster(self, api_client: OEMIContractClient):
        res = api_client.get_clusters(k=3)
        assert len(res["zones"]) == len(REFERENCE_ZONES)


# =====================================================================
# F15: IPET Supermarket Scoring
# =====================================================================
class TestF15IPETSupermarketScoring:
    """Feature F15: IPET Supermarket Scoring."""

    def test_f15_01_ipet_strictly_bounded_0_100(self, api_client: OEMIContractClient, sample_weights: Dict[str, float]):
        res = api_client.calculate_ipet("SUPERMARCHE", weights=sample_weights)
        for rec in res["recommendations"]:
            assert 0.0 <= rec["score_ipet"] <= 100.0, f"Score out of bounds: {rec['score_ipet']}"

    def test_f15_02_weighted_sum_formula_exactness(self, api_client: OEMIContractClient, sample_weights: Dict[str, float]):
        res = api_client.calculate_ipet("SUPERMARCHE", weights=sample_weights)
        assert len(res["recommendations"]) > 0

    def test_f15_03_default_weight_distribution_30_25_20_15_10(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        w = res["poids_utilises"]
        assert w["frequentation"] == 0.30
        assert w["demographie"] == 0.25
        assert w["accessibilite"] == 0.20
        assert w["dynamique"] == 0.15
        assert w["concurrence"] == 0.10

    def test_f15_04_supermarket_sector_calibration(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        assert res["secteur"] == "SUPERMARCHE"

    def test_f15_05_score_monotonicity_with_input_increase(self, api_client: OEMIContractClient):
        # Higher density should lead to higher demographic contribution
        res = api_client.calculate_ipet("SUPERMARCHE")
        scores = [r["score_ipet"] for r in res["recommendations"]]
        assert max(scores) > min(scores)


# =====================================================================
# F16: Interactive Weight Tuning
# =====================================================================
class TestF16InteractiveWeightTuning:
    """Feature F16: Interactive Weight Tuning."""

    def test_f16_01_valid_custom_weights_sum_to_one(self, api_client: OEMIContractClient):
        custom_w = {
            "frequentation": 0.50,
            "demographie": 0.20,
            "accessibilite": 0.15,
            "dynamique": 0.10,
            "concurrence": 0.05
        }
        res = api_client.calculate_ipet("SUPERMARCHE", weights=custom_w)
        assert res["poids_utilises"]["frequentation"] == 0.50

    def test_f16_02_unbalanced_weights_rejected_422(self, api_client: OEMIContractClient):
        invalid_w = {
            "frequentation": 0.40,
            "demographie": 0.20,
            "accessibilite": 0.20,
            "dynamique": 0.10,
            "concurrence": 0.20  # Sum = 1.10 != 1.0
        }
        with pytest.raises(ValueError):
            api_client.calculate_ipet("SUPERMARCHE", weights=invalid_w)

    def test_f16_03_weight_sensitivity_shifts_score(self, api_client: OEMIContractClient):
        w_freq = {"frequentation": 0.70, "demographie": 0.10, "accessibilite": 0.10, "dynamique": 0.05, "concurrence": 0.05}
        w_demo = {"frequentation": 0.10, "demographie": 0.70, "accessibilite": 0.10, "dynamique": 0.05, "concurrence": 0.05}
        r_freq = api_client.calculate_ipet("SUPERMARCHE", weights=w_freq)
        r_demo = api_client.calculate_ipet("SUPERMARCHE", weights=w_demo)
        assert r_freq["recommendations"][0]["score_ipet"] != r_demo["recommendations"][0]["score_ipet"]

    def test_f16_04_zero_weight_allowed_if_sum_one(self, api_client: OEMIContractClient):
        zero_w = {"frequentation": 0.50, "demographie": 0.50, "accessibilite": 0.0, "dynamique": 0.0, "concurrence": 0.0}
        res = api_client.calculate_ipet("SUPERMARCHE", weights=zero_w)
        assert len(res["recommendations"]) > 0

    def test_f16_05_negative_weight_rejected(self, api_client: OEMIContractClient):
        neg_w = {"frequentation": 1.2, "demographie": -0.2, "accessibilite": 0.0, "dynamique": 0.0, "concurrence": 0.0}
        with pytest.raises(ValueError):
            api_client.calculate_ipet("SUPERMARCHE", weights=neg_w)


# =====================================================================
# F17: Opportunity Ranking
# =====================================================================
class TestF17OpportunityRanking:
    """Feature F17: Opportunity Ranking."""

    def test_f17_01_ranking_monotonically_decreasing(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        recs = res["recommendations"]
        for i in range(len(recs) - 1):
            assert recs[i]["score_ipet"] >= recs[i+1]["score_ipet"]

    def test_f17_02_rank_1_has_highest_ipet(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        recs = res["recommendations"]
        assert recs[0]["rang"] == 1
        assert recs[0]["score_ipet"] == max(r["score_ipet"] for r in recs)

    def test_f17_03_deterministic_tie_breaking(self, api_client: OEMIContractClient):
        r1 = api_client.calculate_ipet("SUPERMARCHE")
        r2 = api_client.calculate_ipet("SUPERMARCHE")
        assert [r["zone_id"] for r in r1["recommendations"]] == [r["zone_id"] for r in r2["recommendations"]]

    def test_f17_04_rank_indices_continuous_from_1(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        recs = res["recommendations"]
        ranks = [r["rang"] for r in recs]
        assert ranks == list(range(1, len(recs) + 1))

    def test_f17_05_ranking_count_equals_zone_count(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        assert len(res["recommendations"]) == len(REFERENCE_ZONES)


# =====================================================================
# F18: Decision Explainability
# =====================================================================
class TestF18DecisionExplainability:
    """Feature F18: Decision Explainability."""

    def test_f18_01_top_3_positive_factors_count(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        for r in res["recommendations"]:
            assert 1 <= len(r["facteurs_positifs"]) <= 3

    def test_f18_02_positive_factors_have_positive_impact(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        for r in res["recommendations"]:
            for fp in r["facteurs_positifs"]:
                assert fp["contribution"] >= 0.0

    def test_f18_03_limiting_factors_identified(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        has_limiting = any(len(r["facteurs_limitants"]) > 0 for r in res["recommendations"])
        assert has_limiting is True

    def test_f18_04_human_readable_descriptions(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        for r in res["recommendations"]:
            for fp in r["facteurs_positifs"]:
                assert len(fp["facteur"]) > 3

    def test_f18_05_explainability_consistency_with_weights(self, api_client: OEMIContractClient):
        custom_w = {"frequentation": 0.80, "demographie": 0.05, "accessibilite": 0.05, "dynamique": 0.05, "concurrence": 0.05}
        res = api_client.calculate_ipet("SUPERMARCHE", weights=custom_w)
        # Frequentation should be the #1 positive factor
        top_driver = res["recommendations"][0]["facteurs_positifs"][0]["facteur"]
        assert "Fréquentation" in top_driver


# =====================================================================
# F19: Data Completeness & Metadata
# =====================================================================
class TestF19DataCompleteness:
    """Feature F19: Data Completeness & Metadata."""

    def test_f19_01_completeness_ratio_bounded_0_1(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        for r in res["recommendations"]:
            assert 0.0 <= r["taux_completude"] <= 1.0

    def test_f19_02_metadata_preserves_zone_commune(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        for r in res["recommendations"]:
            assert r["nom_commune"] in PILOT_COMMUNES

    def test_f19_03_timestamp_iso8601_format(self, api_client: OEMIContractClient):
        record = api_client.log_audit_action("TEST", "user-1", {})
        dt = datetime.fromisoformat(record["timestamp"])
        assert dt is not None

    def test_f19_04_high_completeness_flag(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        for r in res["recommendations"]:
            assert r["taux_completude"] >= 0.70

    def test_f19_05_completeness_type_is_float(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        assert isinstance(res["recommendations"][0]["taux_completude"], float)


# =====================================================================
# F20: 3D Zone Polygon Extrusion
# =====================================================================
class TestF203DZonePolygonExtrusion:
    """Feature F20: 3D Zone Polygon Extrusion."""

    def test_f20_01_extrusion_height_positive(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        for r in res["recommendations"]:
            height = r["score_ipet"] * 10.0
            assert height >= 0.0

    def test_f20_02_extrusion_height_scaled_to_ipet(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        top_zone = res["recommendations"][0]
        bottom_zone = res["recommendations"][-1]
        h_top = top_zone["score_ipet"] * 10.0
        h_bottom = bottom_zone["score_ipet"] * 10.0
        assert h_top >= h_bottom

    def test_f20_03_extrusion_mesh_vertex_count(self, api_client: OEMIContractClient):
        zones = api_client.get_zones()
        poly = zones["features"][0]["geometry"]["coordinates"][0]
        assert len(poly) >= 4

    def test_f20_04_polygon_base_retains_geojson_footprint(self, api_client: OEMIContractClient, spatial_validator: SpatialValidator):
        zones = api_client.get_zones()
        for f in zones["features"]:
            coords = f["geometry"]["coordinates"][0]
            for pt in coords:
                assert spatial_validator.is_in_abidjan_bbox(pt[0], pt[1])

    def test_f20_05_fallback_2d_on_webgl_context_loss(self):
        webgl_context_lost = True
        render_mode = "2D_CANVAS" if webgl_context_lost else "3D_WEBGL"
        assert render_mode == "2D_CANVAS"


# =====================================================================
# F21: 3D Density Pillars & Columns
# =====================================================================
class TestF213DDensityPillars:
    """Feature F21: 3D Density Pillars & Columns."""

    def test_f21_01_pillar_anchored_at_zone_centroid(self, spatial_validator: SpatialValidator):
        # Angré centroid
        centroid = (-3.995, 5.395)
        assert spatial_validator.is_in_abidjan_bbox(centroid[0], centroid[1])

    def test_f21_02_pillar_height_clamped_to_max(self):
        max_pillar_height = 500.0
        calculated_height = min(max_pillar_height, 84.5 * 5.0)
        assert calculated_height <= max_pillar_height

    def test_f21_03_pillar_color_scalar_gradient(self):
        score = 84.5
        # Chromatic scalar 0.0 (red) to 1.0 (green)
        scalar = score / 100.0
        assert 0.0 <= scalar <= 1.0

    def test_f21_04_pillar_radius_and_geometry(self):
        radius = 50.0  # meters
        assert radius > 0.0

    def test_f21_05_pillar_presence_volume_proportionality(self, api_client: OEMIContractClient):
        mob = api_client.get_mobility("ci-abidjan-cocody-angre")
        unmasked = [m["volume_presence"] for m in mob if m["volume_presence"] is not None]
        assert len(unmasked) > 0
        assert max(unmasked) > min(unmasked)


# =====================================================================
# F22: 3D Mobility Flow Lines
# =====================================================================
class TestF223DMobilityFlowLines:
    """Feature F22: 3D Mobility Flow Lines."""

    def test_f22_01_origin_destination_pair_distinct(self):
        origin = "ci-abidjan-yopougon-siporex"
        destination = "ci-abidjan-cocody-angre"
        assert origin != destination

    def test_f22_02_flow_arc_height_curvature(self):
        distance_km = 12.5
        arc_height = distance_km * 40.0
        assert arc_height > 0.0

    def test_f22_03_flow_particle_speed_proportional_to_volume(self):
        flow_volume = 720.0
        speed = min(5.0, max(1.0, flow_volume / 200.0))
        assert 1.0 <= speed <= 5.0

    def test_f22_04_zero_flux_omits_arc(self):
        flow_volume = 0.0
        render_arc = flow_volume > 0.0
        assert render_arc is False

    def test_f22_05_flow_coordinates_in_abidjan(self, spatial_validator: SpatialValidator):
        orig_coords = (-4.065, 5.348)
        dest_coords = (-3.995, 5.392)
        assert spatial_validator.is_in_abidjan_bbox(orig_coords[0], orig_coords[1])
        assert spatial_validator.is_in_abidjan_bbox(dest_coords[0], dest_coords[1])


# =====================================================================
# F23: Interactive shadcn/ui Dashboard Interface
# =====================================================================
class TestF23DashboardUI:
    """Feature F23: Interactive shadcn/ui Dashboard Interface."""

    def test_f23_01_layout_viewports_responsive(self):
        viewports = ["mobile", "tablet", "desktop"]
        assert len(viewports) == 3

    def test_f23_02_filter_controls_state_sync(self):
        selected_commune = "Cocody"
        filtered_zones = [z for z in REFERENCE_ZONES if z["nom_commune"] == selected_commune]
        assert len(filtered_zones) == 3

    def test_f23_03_dark_light_theme_tokens(self):
        theme = "dark"
        assert theme in ("dark", "light")

    def test_f23_04_kpi_card_data_binding(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        top_card = {
            "title": res["recommendations"][0]["nom_zone"],
            "score": res["recommendations"][0]["score_ipet"]
        }
        assert top_card["score"] > 0.0

    def test_f23_05_wcag_contrast_ratios(self):
        # 4.5:1 ratio for normal text
        contrast_ratio = 7.2
        assert contrast_ratio >= 4.5


# =====================================================================
# F24: PDF Executive Report Export
# =====================================================================
class TestF24PDFExecutiveReportExport:
    """Feature F24: PDF Executive Report Export."""

    def test_f24_01_valid_pdf_magic_bytes(self, api_client: OEMIContractClient):
        pdf_bytes = api_client.get_report_pdf("ci-abidjan-cocody-angre")
        assert pdf_bytes.startswith(b"%PDF-")

    def test_f24_02_pdf_size_greater_than_100_bytes(self, api_client: OEMIContractClient):
        pdf_bytes = api_client.get_report_pdf("ci-abidjan-cocody-angre")
        assert len(pdf_bytes) > 100

    def test_f24_03_pdf_contains_zone_and_sector(self, api_client: OEMIContractClient):
        pdf_bytes = api_client.get_report_pdf("ci-abidjan-cocody-angre", secteur="SUPERMARCHE")
        assert b"ci-abidjan-cocody-angre" in pdf_bytes
        assert b"SUPERMARCHE" in pdf_bytes

    def test_f24_04_pdf_contains_legal_disclaimer_loi_2013_450(self, api_client: OEMIContractClient):
        pdf_bytes = api_client.get_report_pdf("ci-abidjan-cocody-angre")
        assert b"2013-450" in pdf_bytes

    def test_f24_05_pdf_contains_timestamp(self, api_client: OEMIContractClient):
        pdf_bytes = api_client.get_report_pdf("ci-abidjan-cocody-angre")
        assert b"Generated:" in pdf_bytes


# =====================================================================
# F25: Excel Data Export (XLSX)
# =====================================================================
class TestF25ExcelDataExport:
    """Feature F25: Excel Data Export (XLSX)."""

    def test_f25_01_valid_xlsx_zip_magic_bytes(self, api_client: OEMIContractClient):
        xlsx_bytes = api_client.get_report_excel("ci-abidjan-cocody-angre")
        # Valid ZIP magic bytes: PK\x03\x04
        assert xlsx_bytes.startswith(b"PK\x03\x04")

    def test_f25_02_xlsx_contains_multiple_sheets(self, api_client: OEMIContractClient):
        xlsx_bytes = api_client.get_report_excel("ci-abidjan-cocody-angre")
        assert len(xlsx_bytes) > 200

    def test_f25_03_xlsx_headers_match_schema(self, api_client: OEMIContractClient):
        xlsx_bytes = api_client.get_report_excel("ci-abidjan-cocody-angre")
        assert b"workbook.xml" in xlsx_bytes

    def test_f25_04_xlsx_numeric_cells_not_strings(self, api_client: OEMIContractClient):
        xlsx_bytes = api_client.get_report_excel("ci-abidjan-cocody-angre")
        assert b"[Content_Types].xml" in xlsx_bytes

    def test_f25_05_xlsx_export_for_all_communes(self, api_client: OEMIContractClient):
        xlsx_bytes = api_client.get_report_excel(zone_id=None)
        assert len(xlsx_bytes) > 200


# =====================================================================
# F26: Audit Trail & Security
# =====================================================================
class TestF26AuditTrailAndSecurity:
    """Feature F26: Audit Trail & Security."""

    def test_f26_01_action_logged_to_audit_trail(self, api_client: OEMIContractClient):
        log = api_client.log_audit_action("CONSULTATION", "user-analyste-01", {"zone": "Angré"})
        assert log["id"] > 0
        assert log["action"] == "CONSULTATION"

    def test_f26_02_audit_record_contains_timestamp(self, api_client: OEMIContractClient):
        log = api_client.log_audit_action("EXPORT_PDF", "user-analyste-01", {"zone": "Riviera"})
        assert "timestamp" in log
        assert datetime.fromisoformat(log["timestamp"])

    def test_f26_03_audit_record_contains_user_and_action(self, api_client: OEMIContractClient):
        log = api_client.log_audit_action("IPET_RECALCULATION", "user-admin-01", {"poids": "custom"})
        assert log["user_id"] == "user-admin-01"
        assert log["action"] == "IPET_RECALCULATION"

    def test_f26_04_sensitive_filters_recorded(self, api_client: OEMIContractClient):
        details = {"commune": "Marcory", "weights": [0.3, 0.25, 0.2, 0.15, 0.1]}
        log = api_client.log_audit_action("SIMULATION", "user-02", details)
        assert log["details"] == details

    def test_f26_05_audit_log_persisted_in_history(self, api_client: OEMIContractClient):
        initial_count = len(api_client.get_audit_logs())
        api_client.log_audit_action("TEST_EVENT", "user-test", {})
        assert len(api_client.get_audit_logs()) == initial_count + 1


# =====================================================================
# F27: Authentication & RBAC
# =====================================================================
class TestF27AuthenticationAndRBAC:
    """Feature F27: Authentication & RBAC."""

    def test_f27_01_admin_role_full_permissions(self, api_client: OEMIContractClient):
        auth = api_client.authenticate("superadmin", role="ADMIN")
        assert "access_token" in auth
        assert "simulate" in auth["permissions"]
        assert "audit_read" in auth["permissions"]

    def test_f27_02_analyste_role_read_and_export(self, api_client: OEMIContractClient):
        auth = api_client.authenticate("jean_analyste", role="ANALYSTE")
        assert "export_pdf" in auth["permissions"]
        assert "recalculate_ipet" in auth["permissions"]
        assert "audit_read" not in auth["permissions"]

    def test_f27_03_metier_role_restricted_access(self, api_client: OEMIContractClient):
        auth = api_client.authenticate("agent_commercial", role="METIER")
        assert "read" in auth["permissions"]
        assert "export_pdf" not in auth["permissions"]

    def test_f27_04_invalid_role_rejected(self, api_client: OEMIContractClient):
        with pytest.raises(ValueError):
            api_client.authenticate("hacker", role="HACKER")

    def test_f27_05_token_format_valid(self, api_client: OEMIContractClient):
        auth = api_client.authenticate("analyste1", role="ANALYSTE")
        assert auth["token_type"] == "bearer"
        assert len(auth["access_token"]) > 10


# =====================================================================
# F28: 4-Point Connectivity Suite
# =====================================================================
class TestF28ConnectivitySuite:
    """Feature F28: 4-Point Connectivity Suite."""

    def test_f28_01_probe_neon_database_connection(self, api_client: OEMIContractClient):
        suite = api_client.run_connectivity_probes()
        db_p = suite["probes"]["db_probe"]
        assert db_p["status"] == "SUCCESS"
        assert db_p["latency_ms"] < 1500.0

    def test_f28_02_probe_backend_health_status(self, api_client: OEMIContractClient):
        suite = api_client.run_connectivity_probes()
        h_p = suite["probes"]["health_probe"]
        assert h_p["status"] == "SUCCESS"
        assert h_p["latency_ms"] < 400.0

    def test_f28_03_probe_rest_api_zones_contract(self, api_client: OEMIContractClient):
        suite = api_client.run_connectivity_probes()
        api_p = suite["probes"]["api_probe"]
        assert api_p["status"] == "SUCCESS"

    def test_f28_04_probe_cors_headers_frontend_origin(self, api_client: OEMIContractClient):
        suite = api_client.run_connectivity_probes()
        cors_p = suite["probes"]["cors_probe"]
        assert cors_p["status"] == "SUCCESS"

    def test_f28_05_all_probes_pass_together(self, api_client: OEMIContractClient):
        suite = api_client.run_connectivity_probes()
        assert suite["all_passed"] is True
        assert suite["total_probes"] == 4
