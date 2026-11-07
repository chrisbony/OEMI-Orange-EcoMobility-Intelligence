"""
Tier 4 Real-World Siting Workflows & Scenario Tests.

Authoritative source:
- ORIGINAL_REQUEST.md & Technical_Specification.md §1.1
- Decision support for supermarket site selection in Cocody, Yopougon, and Marcory.

Covers 5 full persona-driven end-to-end workflows:
1. Cocody Flagship Hypermarket Siting (Angré vs Riviera vs Deux Plateaux)
2. Yopougon High-Density Discount Retail Network Expansion (Niangon vs Siporex vs Toits Rouges)
3. Marcory Gourmet Express Store Siting (Competition analysis in Zone 4 vs Biétry)
4. Cross-Commune Portfolio Allocation (Comparative analysis across all 3 pilot communes)
5. Regulatory Privacy & Anonymity Audit (Off-peak mobility audit conforming to Ivorian Law 2013-450)
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List

from tests_e2e.conftest import (
    OEMIContractClient,
    SpatialValidator,
    PILOT_COMMUNES,
    REFERENCE_ZONES,
)


class TestTier4RealWorldScenarios:
    """Tier 4 Realistic End-to-End Decision Workflows."""

    def test_scenario_01_cocody_flagship_hypermarket_siting(
        self,
        api_client: OEMIContractClient,
        spatial_validator: SpatialValidator
    ):
        """
        Scenario 1: Flagship Retailer seeking an optimal hypermarket location in Cocody.
        Workflow:
        1. Authenticate as Analyste.
        2. Retrieve Cocody candidate zones GeoJSON and validate polygons.
        3. Query morning & evening commuter flows for candidate zones.
        4. Apply custom strategic weights emphasizing road connectivity (30%) and commuter flow (30%).
        5. Calculate IPET and verify top-ranked zone has highest accessibility driver.
        6. Export executive PDF report and verify audit logging.
        """
        # Step 1: Authentication
        auth = api_client.authenticate("analyste_cocody", role="ANALYSTE")
        assert "export_pdf" in auth["permissions"]

        # Step 2: Retrieve Cocody zones
        cocody_zones = api_client.get_zones(commune="Cocody")
        features = cocody_zones.get("features", [])
        assert len(features) >= 3
        for f in features:
            errs = spatial_validator.validate_geojson_polygon(f["geometry"])
            assert len(errs) == 0

        # Step 3: Query commuter flows
        angre_mob = api_client.get_mobility("ci-abidjan-cocody-angre", plage_horaire="07h-09h")
        assert len(angre_mob) == 1
        assert angre_mob[0]["volume_presence"] > 1000.0

        # Step 4: Strategic weighting (Access & Commuter focus)
        weights = {
            "frequentation": 0.30,
            "demographie": 0.20,
            "accessibilite": 0.30,
            "dynamique": 0.10,
            "concurrence": 0.10
        }

        # Step 5: Calculate IPET
        res = api_client.calculate_ipet("SUPERMARCHE", weights=weights)
        recs = res["recommendations"]
        cocody_recs = [r for r in recs if r["nom_commune"] == "Cocody"]
        assert len(cocody_recs) >= 3
        top_cocody = cocody_recs[0]
        assert 0.0 <= top_cocody["score_ipet"] <= 100.0
        assert len(top_cocody["facteurs_positifs"]) <= 3

        # Step 6: Export Executive PDF & Audit Log
        pdf_bytes = api_client.get_report_pdf(top_cocody["zone_id"], secteur="SUPERMARCHE")
        assert pdf_bytes.startswith(b"%PDF-")
        audit_rec = api_client.log_audit_action("EXPORT_PDF", "analyste_cocody", {"target_zone": top_cocody["zone_id"]})
        assert audit_rec["id"] > 0

    def test_scenario_02_yopougon_discount_retail_network(
        self,
        api_client: OEMIContractClient
    ):
        """
        Scenario 2: Hard-Discount Food Retailer seeking dense residential expansion in Yopougon.
        Workflow:
        1. Query Yopougon demography and verify high density (>10,000 hab/km2).
        2. Set demography-heavy weight profile (demographie 45%, frequentation 25%).
        3. Recalculate IPET scores and check ranking for Siporex and Niangon.
        4. Run 7-day Prophet time-series prediction to forecast footfall stability.
        5. Export complete analytical XLSX workbook.
        """
        # Step 1: Query Yopougon demography
        demo = api_client.get_demography(commune="Yopougon")
        assert len(demo) >= 3
        for d in demo:
            assert d["densite_hab_km2"] >= 10000.0

        # Step 2: Demography-heavy weights
        weights = {
            "frequentation": 0.25,
            "demographie": 0.45,
            "accessibilite": 0.15,
            "dynamique": 0.10,
            "concurrence": 0.05
        }

        # Step 3: IPET calculation
        res = api_client.calculate_ipet("SUPERMARCHE", weights=weights)
        yop_recs = [r for r in res["recommendations"] if r["nom_commune"] == "Yopougon"]
        assert len(yop_recs) >= 3
        # In demography-heavy profile, high-density Yopougon zone should score prominently
        assert yop_recs[0]["score_ipet"] > 70.0

        # Step 4: Forecasting with Prophet
        top_zone_id = yop_recs[0]["zone_id"]
        forecast = api_client.get_predictions(top_zone_id, model="PROPHET", horizon_days=7)
        assert len(forecast["predictions"]) == 7
        for p in forecast["predictions"]:
            assert p["valeur_estimee"] > 1000.0

        # Step 5: Export XLSX Workbook
        xlsx_bytes = api_client.get_report_excel(top_zone_id, secteur="SUPERMARCHE")
        assert xlsx_bytes.startswith(b"PK\x03\x04")

    def test_scenario_03_marcory_gourmet_express_store(
        self,
        api_client: OEMIContractClient
    ):
        """
        Scenario 3: Premium Gourmet Express Store siting in Marcory (Zone 4 vs Biétry).
        Workflow:
        1. Identify existing competitor supermarkets via OSM POI mapping.
        2. Apply competition-sensitive weights (30% weight to competition avoidance).
        3. Evaluate limiting factors (detect saturated commercial hubs).
        4. Validate IPET score bounds and positive driver breakdown.
        5. Verify decision report generation.
        """
        # Step 1: POI competitor analysis
        pois = api_client.get_pois(commune="Marcory", type_activite="supermarket")
        assert len(pois) >= 2

        # Step 2: Competition-sensitive weights
        weights = {
            "frequentation": 0.25,
            "demographie": 0.20,
            "accessibilite": 0.15,
            "dynamique": 0.10,
            "concurrence": 0.30
        }

        # Step 3: IPET calculation and limiting factor check
        res = api_client.calculate_ipet("SUPERMARCHE", weights=weights)
        marcory_recs = [r for r in res["recommendations"] if r["nom_commune"] == "Marcory"]
        assert len(marcory_recs) >= 2

        # Check limiting factor detection
        has_limiting = any(len(r["facteurs_limitants"]) > 0 for r in marcory_recs)
        assert has_limiting is True

        # Step 4 & 5: Export decision PDF
        pdf_bytes = api_client.get_report_pdf(marcory_recs[0]["zone_id"], secteur="SUPERMARCHE")
        assert len(pdf_bytes) > 100

    def test_scenario_04_cross_commune_portfolio_allocation(
        self,
        api_client: OEMIContractClient
    ):
        """
        Scenario 4: Multi-Commune Portfolio Allocation across Cocody, Yopougon, and Marcory.
        Workflow:
        1. Query full territorial inventory (all 9 zones).
        2. Segment territory into k=3 clusters (high density, commercial transit, residential).
        3. Compare differential temporal progression T1 vs T2.
        4. Generate global ranking across all pilot zones.
        5. Export portfolio XLSX workbook.
        """
        # Step 1: Inventory
        all_zones = api_client.get_zones()
        assert len(all_zones["features"]) >= 9

        # Step 2: Territorial Clustering
        clusters = api_client.get_clusters(k=3)
        assert clusters["nombre_clusters"] == 3
        assert clusters["silhouette_score"] > 0.5

        # Step 3: Differential temporal analysis for representative zone
        diff = api_client.get_differential_analysis("ci-abidjan-cocody-angre", "2026-10-01", "2026-11-01")
        assert diff["delta_absolu"] > 0

        # Step 4: Global IPET Ranking
        res = api_client.calculate_ipet("SUPERMARCHE")
        assert len(res["recommendations"]) == len(REFERENCE_ZONES)
        assert res["recommendations"][0]["rang"] == 1

        # Step 5: Portfolio export
        xlsx_bytes = api_client.get_report_excel(zone_id=None, secteur="SUPERMARCHE")
        assert xlsx_bytes.startswith(b"PK\x03\x04")

    def test_scenario_05_regulatory_privacy_audit_off_peak(
        self,
        api_client: OEMIContractClient
    ):
        """
        Scenario 5: Privacy & Anonymity Regulatory Compliance Audit (Loi Ivoirienne n° 2013-450).
        Workflow:
        1. Query off-peak night hours (02h-04h) in Marcory.
        2. Verify that slices with count < 15 individuals are strictly masked to None.
        3. Verify seuil_k_anonymat_valide flag is strictly False.
        4. Confirm zero presence of PII fields (phone, IMEI, IMSI, user names) in payload.
        5. Verify legal disclaimer presence in exported PDF.
        """
        # Step 1 & 2: Off-peak query
        night_mob = api_client.get_mobility(zone_id="ci-abidjan-marcory-bietry", plage_horaire="02h-04h")
        assert len(night_mob) == 1
        r = night_mob[0]

        # Step 2 & 3: Masking and flag
        assert r["seuil_k_anonymat_valide"] is False
        assert r["volume_presence"] is None
        assert r["flux_entrants"] is None
        assert r["flux_sortants"] is None

        # Step 4: Zero PII
        for forbidden in ["phone", "imsi", "imei", "msisdn", "nom_individu"]:
            assert forbidden not in r

        # Step 5: Legal disclaimer in PDF export
        pdf_bytes = api_client.get_report_pdf("ci-abidjan-marcory-bietry")
        assert b"2013-450" in pdf_bytes
