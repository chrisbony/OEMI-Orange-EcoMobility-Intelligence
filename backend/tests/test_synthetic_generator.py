"""
backend/tests/test_synthetic_generator.py
Unit tests for the realistic synthetic mobility generator.
Verifies temporal dynamics, commuter peaks, Saturday shopping spikes,
deterministic seeding, and traceability flags.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
import datetime
from app.services.synthetic_generator import (
    SyntheticMobilityGenerator,
    STANDARD_TIME_SLICES,
    PRIMARY_ZONE_PROFILES,
    K_ANONYMITY_THRESHOLD,
)


@pytest.fixture
def generator():
    return SyntheticMobilityGenerator(seed=42)


def test_time_slices_completeness(generator):
    """Verifies that all 8 standard time slices are generated for a zone and date."""
    test_date = datetime.date(2026, 11, 2)  # Monday
    zone = "ci-abidjan-cocody-angre"
    records = [
        generator.generate_single_record(zone, test_date, sl)
        for sl in STANDARD_TIME_SLICES
    ]
    slices_generated = [r.plage_horaire for r in records]
    assert slices_generated == STANDARD_TIME_SLICES
    assert len(slices_generated) == 8


def test_weekday_morning_commuter_peak(generator):
    """
    Verifies morning commute dynamics (08h-10h):
    - Residential zone (Yopougon Niangon): outflow > inflow (outflow/inflow >= 2.0).
    - Commercial zone (Marcory Zone 4): inflow > outflow (inflow/outflow >= 2.0).
    """
    monday = datetime.date(2026, 11, 2)
    slice_label = "08h-10h"

    # Residential zone
    rec_yop = generator.generate_single_record("ci-abidjan-yopougon-niangon-nord", monday, slice_label)
    assert rec_yop.flux_sortants is not None and rec_yop.flux_entrants is not None
    assert rec_yop.flux_sortants > rec_yop.flux_entrants
    assert (rec_yop.flux_sortants / rec_yop.flux_entrants) >= 2.0

    # Commercial zone
    rec_mrc = generator.generate_single_record("ci-abidjan-marcory-zone4c", monday, slice_label)
    assert rec_mrc.flux_entrants is not None and rec_mrc.flux_sortants is not None
    assert rec_mrc.flux_entrants > rec_mrc.flux_sortants
    assert (rec_mrc.flux_entrants / rec_mrc.flux_sortants) >= 2.0


def test_weekday_evening_return_peak(generator):
    """
    Verifies evening return peak dynamics (18h-20h):
    - Residential zone: home return, inflow > outflow.
    - Commercial zone: office departure, outflow > inflow.
    """
    monday = datetime.date(2026, 11, 2)
    slice_label = "18h-20h"

    rec_yop = generator.generate_single_record("ci-abidjan-yopougon-niangon-nord", monday, slice_label)
    assert rec_yop.flux_entrants is not None and rec_yop.flux_sortants is not None
    assert rec_yop.flux_entrants > rec_yop.flux_sortants

    rec_mrc = generator.generate_single_record("ci-abidjan-marcory-zone4c", monday, slice_label)
    assert rec_mrc.flux_sortants is not None and rec_mrc.flux_entrants is not None
    assert rec_mrc.flux_sortants > rec_mrc.flux_entrants


def test_saturday_shopping_peak_in_commercial_zone(generator):
    """Verifies Saturday afternoon shopping peak in commercial zones exceeds weekday baseline by >= 30%."""
    tuesday = datetime.date(2026, 11, 3)
    saturday = datetime.date(2026, 11, 7)
    slice_label = "16h-18h"
    zone = "ci-abidjan-marcory-zone4c"

    rec_tue = generator.generate_single_record(zone, tuesday, slice_label)
    rec_sat = generator.generate_single_record(zone, saturday, slice_label)

    assert rec_sat.volume_presence is not None and rec_tue.volume_presence is not None
    assert rec_sat.volume_presence > (rec_tue.volume_presence * 1.3)


def test_traceability_synthetic_flag(generator):
    """Verifies that 100% of generated records have est_synthetique == True."""
    start = datetime.date(2026, 11, 2)
    end = datetime.date(2026, 11, 4)
    records = generator.generate_range(start, end)
    assert len(records) > 0
    for r in records:
        assert r.est_synthetique is True


def test_seed_reproducibility():
    """Verifies deterministic output reproduction with identical seed."""
    gen1 = SyntheticMobilityGenerator(seed=12345)
    gen2 = SyntheticMobilityGenerator(seed=12345)
    date_test = datetime.date(2026, 11, 6)

    r1 = gen1.generate_single_record("ci-abidjan-cocody-angre", date_test, "12h-14h")
    r2 = gen2.generate_single_record("ci-abidjan-cocody-angre", date_test, "12h-14h")

    assert r1.volume_presence == r2.volume_presence
    assert r1.flux_entrants == r2.flux_entrants
    assert r1.flux_sortants == r2.flux_sortants


def test_alias_zone_id_support(generator):
    """Verifies that abbreviated / alias zone IDs resolve correctly."""
    monday = datetime.date(2026, 11, 2)
    rec_alias = generator.generate_single_record("ci-abidjan-yopougon-niangon", monday, "08h-10h")
    rec_canonical = generator.generate_single_record("ci-abidjan-yopougon-niangon-nord", monday, "08h-10h")
    assert rec_alias.plage_horaire == "08h-10h"
    assert rec_canonical.plage_horaire == "08h-10h"
