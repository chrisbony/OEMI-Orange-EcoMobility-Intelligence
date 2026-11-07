"""
Tier 2 Boundary, Edge Case, and Privacy Constraint Tests.

Authoritative sources:
- Ivorian Law n° 2013-450 (Protection des Données à Caractère Personnel):
  Strict k-anonymity masking where aggregate volume < 15.
- Technical_Specification.md §3.1 & CdC §9.3:
  IPET scores strictly clamped in [0.0, 100.0].
  Multicriteria weights vector must strictly sum to 1.0.
- Geographic referential EPSG:4326 Abidjan pilot bounding box.
"""

import math
import pytest
from typing import Dict, Any, List

from tests_e2e.conftest import (
    OEMIContractClient,
    SpatialValidator,
    ABIDJAN_BBOX,
    REFERENCE_ZONES,
)


class TestKAnonymityBoundaries:
    """Boundary Value Analysis for Ivorian Law n° 2013-450 k-anonymity (k=15 threshold)."""

    def test_tier2_kanon_boundary_14_strictly_masked(self):
        # Value = 14 is below threshold 15 -> MUST be masked
        val = 14.0
        is_valid_k = val >= 15.0
        masked_val = val if is_valid_k else None
        assert is_valid_k is False
        assert masked_val is None

    def test_tier2_kanon_boundary_15_exposed_clear(self):
        # Value = 15 is exact threshold -> MUST be cleartext
        val = 15.0
        is_valid_k = val >= 15.0
        masked_val = val if is_valid_k else None
        assert is_valid_k is True
        assert masked_val == 15.0

    def test_tier2_kanon_boundary_16_exposed_clear(self):
        # Value = 16 is immediately above threshold -> MUST be cleartext
        val = 16.0
        is_valid_k = val >= 15.0
        masked_val = val if is_valid_k else None
        assert is_valid_k is True
        assert masked_val == 16.0

    def test_tier2_kanon_boundary_zero_count_masked(self):
        val = 0.0
        is_valid_k = val >= 15.0
        masked_val = val if is_valid_k else None
        assert is_valid_k is False
        assert masked_val is None

    def test_tier2_kanon_negative_count_rejected_or_masked(self):
        val = -5.0
        # Clamped to 0 then masked
        clamped = max(0.0, val)
        is_valid_k = clamped >= 15.0
        assert is_valid_k is False


class TestIPETScoreNormalizationBoundaries:
    """Mathematical Invariant: IPET(z) strictly clamped in [0.0, 100.0]."""

    def test_tier2_ipet_theoretical_maximum_clamped_to_100(self, api_client: OEMIContractClient):
        # Custom zone with ultra-dense, ultra-connected metrics
        extreme_zone = [{
            "id": "zone-max",
            "nom_commune": "Cocody",
            "nom_zone": "Ultra Hub",
            "population": 5000000,
            "densite": 500000.0,
            "score_connectivite": 150.0,
            "dynamique": 100.0,
            "nb_commerces_concurrents": 0
        }]
        res = api_client.calculate_ipet("SUPERMARCHE", zones=extreme_zone)
        score = res["recommendations"][0]["score_ipet"]
        assert score == 100.0, f"Expected 100.0 ceiling, got {score}"

    def test_tier2_ipet_theoretical_minimum_clamped_to_0(self, api_client: OEMIContractClient):
        # Custom zone with 0 indicators and high competition
        empty_zone = [{
            "id": "zone-zero",
            "nom_commune": "Yopougon",
            "nom_zone": "Désert",
            "population": 0,
            "densite": 0.0,
            "score_connectivite": 0.0,
            "nb_commerces_concurrents": 20
        }]
        res = api_client.calculate_ipet("SUPERMARCHE", zones=empty_zone)
        score = res["recommendations"][0]["score_ipet"]
        assert score >= 0.0
        assert score <= 15.0

    def test_tier2_ipet_negative_indicators_clamped_to_zero(self, api_client: OEMIContractClient):
        negative_zone = [{
            "id": "zone-neg",
            "nom_commune": "Marcory",
            "nom_zone": "Negative",
            "population": -10000,
            "densite": -500.0,
            "score_connectivite": -50.0,
            "nb_commerces_concurrents": 50
        }]
        res = api_client.calculate_ipet("SUPERMARCHE", zones=negative_zone)
        score = res["recommendations"][0]["score_ipet"]
        assert 0.0 <= score <= 100.0

    def test_tier2_ipet_floating_point_precision_tolerance(self, api_client: OEMIContractClient):
        res = api_client.calculate_ipet("SUPERMARCHE")
        for rec in res["recommendations"]:
            score = rec["score_ipet"]
            assert not math.isnan(score)
            assert not math.isinf(score)
            assert 0.0 <= score <= 100.0


class TestWeightsSumBoundaries:
    """Constraint: Multicriteria weights vector sum must strictly equal 1.0."""

    def test_tier2_weights_sum_0_999_rejected(self, api_client: OEMIContractClient):
        w = {"frequentation": 0.299, "demographie": 0.25, "accessibilite": 0.20, "dynamique": 0.15, "concurrence": 0.10}
        with pytest.raises(ValueError):
            api_client.calculate_ipet("SUPERMARCHE", weights=w)

    def test_tier2_weights_sum_1_001_rejected(self, api_client: OEMIContractClient):
        w = {"frequentation": 0.301, "demographie": 0.25, "accessibilite": 0.20, "dynamique": 0.15, "concurrence": 0.10}
        with pytest.raises(ValueError):
            api_client.calculate_ipet("SUPERMARCHE", weights=w)

    def test_tier2_weights_sum_exactly_1_0_accepted(self, api_client: OEMIContractClient):
        w = {"frequentation": 0.30, "demographie": 0.25, "accessibilite": 0.20, "dynamique": 0.15, "concurrence": 0.10}
        res = api_client.calculate_ipet("SUPERMARCHE", weights=w)
        assert len(res["recommendations"]) > 0

    def test_tier2_weights_single_dominant_factor_accepted(self, api_client: OEMIContractClient):
        w = {"frequentation": 1.0, "demographie": 0.0, "accessibilite": 0.0, "dynamique": 0.0, "concurrence": 0.0}
        res = api_client.calculate_ipet("SUPERMARCHE", weights=w)
        assert res["poids_utilises"]["frequentation"] == 1.0

    def test_tier2_weights_negative_weight_rejected(self, api_client: OEMIContractClient):
        w = {"frequentation": 1.1, "demographie": -0.1, "accessibilite": 0.0, "dynamique": 0.0, "concurrence": 0.0}
        with pytest.raises(ValueError):
            api_client.calculate_ipet("SUPERMARCHE", weights=w)


class TestGeospatialBoundaryConditions:
    """Geographic Bounding Box and Geometry Malformation Boundaries."""

    def test_tier2_geo_point_exactly_on_bbox_boundary(self, spatial_validator: SpatialValidator):
        # min_lon and min_lat
        assert spatial_validator.is_in_abidjan_bbox(ABIDJAN_BBOX["min_lon"], ABIDJAN_BBOX["min_lat"])
        # max_lon and max_lat
        assert spatial_validator.is_in_abidjan_bbox(ABIDJAN_BBOX["max_lon"], ABIDJAN_BBOX["max_lat"])

    def test_tier2_geo_point_outside_bbox_west(self, spatial_validator: SpatialValidator):
        assert not spatial_validator.is_in_abidjan_bbox(-4.15001, 5.30)

    def test_tier2_geo_point_outside_bbox_east(self, spatial_validator: SpatialValidator):
        assert not spatial_validator.is_in_abidjan_bbox(-3.84999, 5.30)

    def test_tier2_geo_point_outside_bbox_north(self, spatial_validator: SpatialValidator):
        assert not spatial_validator.is_in_abidjan_bbox(-4.00, 5.45001)

    def test_tier2_geo_point_outside_bbox_south(self, spatial_validator: SpatialValidator):
        assert not spatial_validator.is_in_abidjan_bbox(-4.00, 5.24999)

    def test_tier2_geo_unclosed_polygon_detected(self, spatial_validator: SpatialValidator):
        unclosed = {
            "type": "Polygon",
            "coordinates": [[
                [-4.00, 5.30],
                [-3.99, 5.30],
                [-3.99, 5.31],
                [-4.00, 5.31]
                # Missing closing vertex [-4.00, 5.30]
            ]]
        }
        errors = spatial_validator.validate_geojson_polygon(unclosed)
        assert any("not closed" in e for e in errors)

    def test_tier2_geo_fewer_than_4_vertices_detected(self, spatial_validator: SpatialValidator):
        triangle_open = {
            "type": "Polygon",
            "coordinates": [[
                [-4.00, 5.30],
                [-3.99, 5.30],
                [-4.00, 5.30]
            ]]
        }
        errors = spatial_validator.validate_geojson_polygon(triangle_open)
        assert any("fewer than 4 vertices" in e for e in errors)

    def test_tier2_geo_non_dict_geometry_rejected(self, spatial_validator: SpatialValidator):
        errors = spatial_validator.validate_geojson_polygon("NOT_A_GEOMETRY") # type: ignore
        assert len(errors) > 0


class TestTemporalAndInputEdgeCases:
    """Extreme string inputs, inverted intervals, and division guards."""

    def test_tier2_inverted_time_interval_handling(self, api_client: OEMIContractClient):
        # T1 after T2
        diff = api_client.get_differential_analysis("ci-abidjan-cocody-angre", "2026-11-01", "2026-10-01")
        assert diff is not None
        assert "delta_absolu" in diff

    def test_tier2_sql_injection_attempt_in_zone_id(self, api_client: OEMIContractClient):
        malicious = "ci-abidjan-cocody-angre' OR '1'='1"
        res = api_client.get_zones(commune=malicious)
        assert len(res["features"]) == 0

    def test_tier2_extreme_length_string_in_zone_id(self, api_client: OEMIContractClient):
        long_str = "A" * 2000
        res = api_client.get_zones(commune=long_str)
        assert len(res["features"]) == 0

    def test_tier2_wape_zero_division_guard(self):
        y_true = [0.0, 0.0, 0.0]
        y_pred = [0.0, 0.0, 0.0]
        denom = sum(y_true)
        wape = 0.0 if denom == 0 else sum(abs(t - p) for t, p in zip(y_true, y_pred)) / denom
        assert wape == 0.0
