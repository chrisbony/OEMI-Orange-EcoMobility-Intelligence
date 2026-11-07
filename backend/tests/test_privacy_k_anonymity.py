"""
backend/tests/test_privacy_k_anonymity.py
Unit and regulatory compliance tests for k-anonymity (Loi CI n° 2013-450) and Zero PII guarantees.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
import datetime
from dataclasses import asdict
from app.services.synthetic_generator import (
    SyntheticMobilityGenerator,
    apply_k_anonymity,
    K_ANONYMITY_THRESHOLD,
)
from app.models.mobility import MobiliteAgregee

FORBIDDEN_PII_FIELDS = {
    "msisdn", "phone", "imei", "imsi", "mac", "mac_address",
    "ip_address", "user_id", "nom_client", "gps_latitude",
    "gps_longitude", "individual_id", "device_id"
}


@pytest.fixture
def generator():
    return SyntheticMobilityGenerator(seed=99)


def test_k_anonymity_masking_under_threshold(generator):
    """Verifies strict masking when volume is below k = 15 individuals."""
    test_date = datetime.date(2026, 11, 2)
    zone = "ci-abidjan-cocody-angre"

    # Force sub-threshold volume
    rec = generator.generate_single_record(zone, test_date, "22h-08h", force_low_volume=True)

    assert rec.seuil_k_anonymat_valide is False
    assert rec.volume_presence is None
    assert rec.flux_entrants is None
    assert rec.flux_sortants is None


def test_k_anonymity_boundary_values():
    """Verifies exact threshold boundary at k = 15.0."""
    # Below threshold (< 15) must be masked
    val, ok = apply_k_anonymity(14.9)
    assert ok is False
    assert val is None

    val, ok = apply_k_anonymity(14.999)
    assert ok is False
    assert val is None

    # At boundary (15.0) must be valid
    val, ok = apply_k_anonymity(15.0)
    assert ok is True
    assert val == 15.0

    # Above threshold (> 15) must be valid
    val, ok = apply_k_anonymity(15.1)
    assert ok is True
    assert val == 15.1

    # Edge cases
    val, ok = apply_k_anonymity(0.0)
    assert ok is False
    assert val is None

    val, ok = apply_k_anonymity(-5.0)
    assert ok is False
    assert val is None

    val, ok = apply_k_anonymity(None)
    assert ok is False
    assert val is None

    # Non-finite float values (NaN, +Inf, -Inf) must be strictly rejected
    val, ok = apply_k_anonymity(float("nan"))
    assert ok is False
    assert val is None

    val, ok = apply_k_anonymity(float("inf"))
    assert ok is False
    assert val is None

    val, ok = apply_k_anonymity(float("-inf"))
    assert ok is False
    assert val is None


def test_zero_pii_audit_on_records(generator):
    """Verifies that no Personally Identifiable Information (PII) is present on mobility records."""
    test_date = datetime.date(2026, 11, 2)
    rec = generator.generate_single_record("ci-abidjan-marcory-zone4c", test_date, "12h-14h")
    data_dict = asdict(rec)

    for field in data_dict.keys():
        assert field.lower() not in FORBIDDEN_PII_FIELDS, f"PII leak detected in record: '{field}'"


def test_zero_pii_audit_on_database_model():
    """Verifies that the MobiliteAgregee database table contains zero individual PII columns."""
    column_names = {c.name.lower() for c in MobiliteAgregee.__table__.columns}
    for field in FORBIDDEN_PII_FIELDS:
        assert field not in column_names, f"PII column detected in MobiliteAgregee table: '{field}'"


def test_range_generation_contains_masked_samples(generator):
    """Verifies that range generation properly enforces k-anonymity on sub-threshold samples."""
    start = datetime.date(2026, 11, 2)
    end = datetime.date(2026, 11, 4)
    records = generator.generate_range(start, end, inject_low_volume_samples=True)

    masked_records = [r for r in records if r.seuil_k_anonymat_valide is False]
    assert len(masked_records) >= 1
    for r in masked_records:
        assert r.volume_presence is None
        assert r.flux_entrants is None
        assert r.flux_sortants is None
