"""
backend/tests/test_privacy_adversarial.py
Adversarial stress harness for k-anonymity engine (Loi CI n° 2013-450) and Zero PII validation.
Designed by challenger_m1_2.
"""
import sys
import math
import datetime
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from app.services.synthetic_generator import (
    SyntheticMobilityGenerator,
    apply_k_anonymity,
    K_ANONYMITY_THRESHOLD,
    SyntheticMobilityRecord,
)
from app.models.mobility import MobiliteAgregee
from app.models.zone import ZoneGeographique
from app.models.demography import Demographie
from app.models.infrastructure import InfrastructureCommerce, AccessibiliteRoutiere
from app.models.prediction import PrevisionFrequentation
from app.models.ipet import ScoreRecommandationIPET
from app.models.audit import Utilisateur, JournalAudit


class TestPrivacyAdversarial:
    """Adversarial challenge suite testing boundary conditions, non-finites, and high-volume invariants."""

    def test_strict_boundary_real_numbers(self):
        """Tests exact float threshold boundary at k = 15.0."""
        # Under threshold: must be masked
        val, ok = apply_k_anonymity(14.9999)
        assert ok is False, f"Expected False for 14.9999, got {ok}"
        assert val is None, f"Expected None for 14.9999, got {val}"

        val, ok = apply_k_anonymity(0.0)
        assert ok is False
        assert val is None

        val, ok = apply_k_anonymity(-5.0)
        assert ok is False
        assert val is None

        val, ok = apply_k_anonymity(-float("inf"))
        assert ok is False
        assert val is None

        # Exact threshold: must be valid
        val, ok = apply_k_anonymity(15.0)
        assert ok is True
        assert val == 15.0

        # Above threshold: must be valid
        val, ok = apply_k_anonymity(15.0001)
        assert ok is True
        assert val == 15.0

    def test_adversarial_non_finite_inputs(self):
        """
        Adversarial test: NaN and +Infinity must NOT be validated as valid k-anonymity.
        They must be masked to (None, False).
        """
        # Test NaN
        val_nan, ok_nan = apply_k_anonymity(float("nan"))
        assert ok_nan is False, f"Vulnerability: apply_k_anonymity(NaN) returned ok={ok_nan}, expected False"
        assert val_nan is None, f"Vulnerability: apply_k_anonymity(NaN) returned val={val_nan}, expected None"

        # Test +Infinity
        val_inf, ok_inf = apply_k_anonymity(float("inf"))
        assert ok_inf is False, f"Vulnerability: apply_k_anonymity(+Inf) returned ok={ok_inf}, expected False"
        assert val_inf is None, f"Vulnerability: apply_k_anonymity(+Inf) returned val={val_inf}, expected None"

    def test_high_volume_10k_synthetic_records_invariant(self):
        """
        Property-based stress test: 10,000+ synthetic mobility records across all zones and time slices.
        Assert invariant:
        - If seuil_k_anonymat_valide is False: volume_presence is None AND flux are None
        - If seuil_k_anonymat_valide is True: volume_presence >= 15.0
        """
        gen = SyntheticMobilityGenerator(seed=42)
        start = datetime.date(2026, 1, 1)
        # 140 days * 9 zones * 8 slices = 10,080 records
        records = gen.generate_range(start, start + datetime.timedelta(days=139), inject_low_volume_samples=True)
        assert len(records) >= 10000

        # Inject 5% random low-volume records to ensure significant coverage of masked branch
        for i in range(0, len(records), 20):
            records[i] = gen.generate_single_record(
                zone_id=records[i].zone_id,
                date_obs=records[i].date_observation,
                slice_label=records[i].plage_horaire,
                force_low_volume=True,
            )

        for rec in records:
            if rec.seuil_k_anonymat_valide is False:
                assert rec.volume_presence is None, f"Leaked volume in masked record: {rec}"
                assert rec.flux_entrants is None, f"Leaked flux_entrants in masked record: {rec}"
                assert rec.flux_sortants is None, f"Leaked flux_sortants in masked record: {rec}"
            else:
                assert rec.volume_presence is not None, f"Missing volume in valid record: {rec}"
                assert rec.volume_presence >= K_ANONYMITY_THRESHOLD, f"Volume < threshold in valid record: {rec}"

    def test_exhaustive_zero_pii_audit(self):
        """Audits all 9 SQLAlchemy models and synthetic records for zero PII."""
        forbidden_substrings = [
            "msisdn", "phone", "telephone", "mobile", "imei", "imsi",
            "mac", "mac_address", "ip_address", "individual_id", "device_id",
            "nom_client", "prenom", "first_name", "last_name", "gps_track"
        ]

        models = [
            ZoneGeographique, MobiliteAgregee, Demographie,
            InfrastructureCommerce, AccessibiliteRoutiere,
            PrevisionFrequentation, ScoreRecommandationIPET,
            Utilisateur, JournalAudit
        ]

        for model in models:
            for col in model.__table__.columns:
                col_lower = col.name.lower()
                for pattern in forbidden_substrings:
                    assert pattern not in col_lower, f"PII pattern '{pattern}' detected in {model.__tablename__}.{col.name}"

