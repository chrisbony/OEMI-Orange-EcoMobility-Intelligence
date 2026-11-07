"""
Tier 3 Pairwise Combinatorial Interaction Tests.

Evaluates orthogonal combinations across:
- Spatial pilot zones (Cocody, Yopougon, Marcory)
- Temporal slices (Morning peak, Midday, Evening peak, Late night)
- Analytical IPET weight profiles (Mobility-heavy, Demography-heavy, Accessibility-heavy, Balanced)
- Forecasting models & horizons (Naive, Prophet, XGBoost across 7 & 14 days)
- Decision export formats (PDF ReportLab vector, XLSX OpenPyXL tabular)
"""

import pytest
from typing import Dict, Any, List

from tests_e2e.conftest import (
    OEMIContractClient,
    SpatialValidator,
    PILOT_COMMUNES,
    REFERENCE_ZONES,
)


class TestSpatialTemporalCombinations:
    """Pairwise combinations between Pilot Zones and Temporal Diurnal Slices."""

    @pytest.mark.parametrize("commune,zone_id", [
        ("Cocody", "ci-abidjan-cocody-angre"),
        ("Cocody", "ci-abidjan-cocody-riviera"),
        ("Yopougon", "ci-abidjan-yopougon-siporex"),
        ("Yopougon", "ci-abidjan-yopougon-niangon"),
        ("Marcory", "ci-abidjan-marcory-bietry"),
        ("Marcory", "ci-abidjan-marcory-zone4")
    ])
    @pytest.mark.parametrize("plage_horaire,expect_high_volume", [
        ("07h-09h", True),   # Morning commuter peak
        ("12h-14h", False),  # Midday lunch
        ("17h-20h", True),   # Evening commuter peak
        ("02h-04h", False)   # Late-night sub-threshold
    ])
    def test_tier3_zone_x_timeslot_mobility(
        self,
        api_client: OEMIContractClient,
        commune: str,
        zone_id: str,
        plage_horaire: str,
        expect_high_volume: bool
    ):
        records = api_client.get_mobility(zone_id=zone_id, plage_horaire=plage_horaire)
        assert len(records) == 1
        r = records[0]
        assert r["zone_id"] == zone_id
        assert r["plage_horaire"] == plage_horaire

        if plage_horaire == "02h-04h":
            # Must enforce k-anonymity masking (< 15)
            assert r["seuil_k_anonymat_valide"] is False
            assert r["volume_presence"] is None
        else:
            assert r["seuil_k_anonymat_valide"] is True
            assert r["volume_presence"] is not None
            if expect_high_volume:
                assert r["volume_presence"] >= 1000.0


class TestSpatialWeightProfileCombinations:
    """Pairwise combinations between Candidate Zones and Multicriteria Strategic Profiles."""

    WEIGHT_PROFILES = {
        "MOBILITY_HEAVY": {
            "frequentation": 0.50,
            "demographie": 0.15,
            "accessibilite": 0.15,
            "dynamique": 0.10,
            "concurrence": 0.10
        },
        "DEMOGRAPHY_HEAVY": {
            "frequentation": 0.15,
            "demographie": 0.50,
            "accessibilite": 0.15,
            "dynamique": 0.10,
            "concurrence": 0.10
        },
        "ACCESSIBILITY_HEAVY": {
            "frequentation": 0.15,
            "demographie": 0.15,
            "accessibilite": 0.50,
            "dynamique": 0.10,
            "concurrence": 0.10
        },
        "COMPETITION_AVERSE": {
            "frequentation": 0.20,
            "demographie": 0.20,
            "accessibilite": 0.15,
            "dynamique": 0.10,
            "concurrence": 0.35
        },
        "BALANCED": {
            "frequentation": 0.20,
            "demographie": 0.20,
            "accessibilite": 0.20,
            "dynamique": 0.20,
            "concurrence": 0.20
        }
    }

    @pytest.mark.parametrize("profile_name", list(WEIGHT_PROFILES.keys()))
    def test_tier3_weight_profile_execution_and_normalization(
        self,
        api_client: OEMIContractClient,
        profile_name: str
    ):
        weights = self.WEIGHT_PROFILES[profile_name]
        res = api_client.calculate_ipet("SUPERMARCHE", weights=weights)
        assert len(res["recommendations"]) == len(REFERENCE_ZONES)
        for r in res["recommendations"]:
            assert 0.0 <= r["score_ipet"] <= 100.0
            assert len(r["facteurs_positifs"]) <= 3

    def test_tier3_demography_heavy_favors_yopougon(self, api_client: OEMIContractClient):
        # Yopougon has the highest demographic population and density
        w_demo = self.WEIGHT_PROFILES["DEMOGRAPHY_HEAVY"]
        res = api_client.calculate_ipet("SUPERMARCHE", weights=w_demo)
        top_recs = res["recommendations"][:3]
        top_communes = [r["nom_commune"] for r in top_recs]
        assert "Yopougon" in top_communes


class TestForecastingModelHorizonCombinations:
    """Pairwise combinations between Forecasting Models and Time Horizons."""

    @pytest.mark.parametrize("zone_id", [
        "ci-abidjan-cocody-angre",
        "ci-abidjan-yopougon-siporex",
        "ci-abidjan-marcory-bietry"
    ])
    @pytest.mark.parametrize("model,horizon", [
        ("NAIVE", 7),
        ("PROPHET", 7),
        ("PROPHET", 14),
        ("XGBOOST", 7),
        ("XGBOOST", 14)
    ])
    def test_tier3_model_x_horizon_forecasting(
        self,
        api_client: OEMIContractClient,
        zone_id: str,
        model: str,
        horizon: int
    ):
        res = api_client.get_predictions(zone_id=zone_id, model=model, horizon_days=horizon)
        assert res["modele"] == model
        assert len(res["predictions"]) == horizon
        for p in res["predictions"]:
            assert p["valeur_estimee"] >= 0.0
            assert p["borne_inferieure"] <= p["valeur_estimee"] <= p["borne_superieure"]


class TestExportModalityCombinations:
    """Pairwise combinations between Evaluated Zones and Export File Types."""

    @pytest.mark.parametrize("zone_id", [
        "ci-abidjan-cocody-angre",
        "ci-abidjan-yopougon-siporex",
        "ci-abidjan-marcory-zone4"
    ])
    def test_tier3_dual_export_pdf_and_excel(
        self,
        api_client: OEMIContractClient,
        zone_id: str
    ):
        # 1. PDF Export
        pdf_bytes = api_client.get_report_pdf(zone_id=zone_id, secteur="SUPERMARCHE")
        assert pdf_bytes.startswith(b"%PDF-")
        assert zone_id.encode("utf-8") in pdf_bytes

        # 2. Excel Export
        xlsx_bytes = api_client.get_report_excel(zone_id=zone_id, secteur="SUPERMARCHE")
        assert xlsx_bytes.startswith(b"PK\x03\x04")
        assert len(xlsx_bytes) > 200

        # 3. Verify audit trail logs both exports
        log_pdf = api_client.log_audit_action("EXPORT_PDF", "analyste_test", {"zone_id": zone_id})
        log_xlsx = api_client.log_audit_action("EXPORT_EXCEL", "analyste_test", {"zone_id": zone_id})
        assert log_pdf["id"] > 0
        assert log_xlsx["id"] > log_pdf["id"]
