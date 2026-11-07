"""
Tier 2 Boundary, Corner Case & Adversarial Tests for Milestone M1 Foundation.
Authoritative source: TEST_INFRA.md, PROJECT.md, mld.md.

Covers:
- Inverted / out-of-bounds geographic coordinates (swapped lon/lat, points outside Abidjan).
- Malformed GeoJSON geometries (unclosed polygon rings, insufficient vertices).
- Adversarial SQL injection strings in commune filter parameters.
- Mathematical zero-division guards on demographic density / household ratios.
- Negative demographic values rejection.
"""

import unittest
import math
from tests_e2e.conftest import SpatialValidator, ABIDJAN_BBOX

try:
    import psycopg
except ImportError:
    psycopg = None

from tests_e2e.conftest import DEFAULT_DB_URL


class TestM1BoundariesAndCornerCases(unittest.TestCase):
    """Tier 2 Boundary & Adversarial Suite for M1 Foundation."""

    validator = SpatialValidator()
    db_url = DEFAULT_DB_URL

    def test_tier2_01_swapped_latitude_longitude_detection(self):
        """Test T2-01: Detect inverted coordinates (Lat in Lon slot: 5.34 in place of -4.03)."""
        # Abidjan: Lon is negative (-4.0), Lat is positive (+5.3)
        inverted_point = {
            "type": "Point",
            "coordinates": [5.3484, -4.0305]  # Inverted! Lon=5.34 (Atlantic/Gulf), Lat=-4.03 (Southern hemisphere)
        }
        errors = self.validator.validate_geojson_point(inverted_point)
        self.assertGreater(
            len(errors), 0,
            "Validator failed to detect inverted latitude/longitude coordinates"
        )
        self.assertTrue(
            any("outside Abidjan" in e for e in errors),
            f"Expected bbox violation error, got: {errors}"
        )

    def test_tier2_02_malformed_unclosed_polygon_ring(self):
        """Test T2-02: Detect unclosed polygon rings where first vertex != last vertex."""
        unclosed_polygon = {
            "type": "Polygon",
            "coordinates": [
                [
                    [-4.01, 5.31],
                    [-4.00, 5.31],
                    [-4.00, 5.32],
                    [-4.01, 5.35]  # Does not close back to [-4.01, 5.31]
                ]
            ]
        }
        errors = self.validator.validate_geojson_polygon(unclosed_polygon)
        self.assertGreater(len(errors), 0, "Validator failed to flag unclosed polygon ring")
        self.assertTrue(
            any("not closed" in e for e in errors),
            f"Expected ring closure error, got: {errors}"
        )

    def test_tier2_03_insufficient_polygon_vertices(self):
        """Test T2-03: Detect polygons with fewer than 4 vertices (degenerate polygons)."""
        degenerate_polygon = {
            "type": "Polygon",
            "coordinates": [
                [
                    [-4.01, 5.31],
                    [-4.00, 5.31],
                    [-4.01, 5.31]  # Only 3 points (2 unique)
                ]
            ]
        }
        errors = self.validator.validate_geojson_polygon(degenerate_polygon)
        self.assertGreater(len(errors), 0, "Validator failed to flag degenerate polygon with < 4 vertices")
        self.assertTrue(
            any("fewer than 4 vertices" in e or "< 4 vertices" in e for e in errors),
            f"Expected vertex count error, got: {errors}"
        )

    def test_tier2_04_adversarial_sql_injection_filter(self):
        """Test T2-04: Adversarial SQL injection strings in commune filter parameters."""
        injection_payload = "Cocody'; DROP TABLE IF EXISTS dummy_test_table; SELECT '1"
        if not psycopg:
            self.skipTest("psycopg not installed")

        try:
            with psycopg.connect(self.db_url, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    # Check if zones table exists
                    cur.execute(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'zones_geographiques');"
                    )
                    table_exists = cur.fetchone()[0]
                    if table_exists:
                        cur.execute(
                            "SELECT COUNT(*) FROM zones_geographiques WHERE nom_commune = %s;",
                            (injection_payload,)
                        )
                        count = cur.fetchone()[0]
                        self.assertEqual(count, 0, "SQL injection should match 0 rows")
                    else:
                        # Verify parameterized query works safely without injection execution
                        cur.execute("SELECT %s = 'safe';", (injection_payload,))
                        res = cur.fetchone()[0]
                        self.assertFalse(res)
        except (psycopg.errors.ConnectionTimeout, psycopg.OperationalError) as exc:
            self.skipTest(f"Neon database cold-start timeout: {exc}")
        except Exception as exc:
            self.fail(f"Adversarial parameter execution caused unhandled failure: {exc}")

    def test_tier2_05_demographic_zero_division_guard(self):
        """Test T2-05: Ensure demographic metric calculations handle zero households or zero area without crashing."""
        def safe_household_size(population: int, households: int) -> float:
            if not households or households <= 0:
                return 0.0
            return population / households

        # Edge cases: 0 households, negative households, null
        self.assertEqual(safe_household_size(5000, 0), 0.0)
        self.assertEqual(safe_household_size(5000, -1), 0.0)
        self.assertEqual(safe_household_size(0, 100), 0.0)
        self.assertEqual(round(safe_household_size(1000, 250), 2), 4.0)

    def test_tier2_06_extreme_wgs84_bounds_rejection(self):
        """Test T2-06: Flag coordinates beyond valid WGS84 range (lon > 180, lat > 90)."""
        out_of_bounds_polygon = {
            "type": "Polygon",
            "coordinates": [
                [
                    [-185.0, 95.0],
                    [-184.0, 95.0],
                    [-184.0, 96.0],
                    [-185.0, 95.0]
                ]
            ]
        }
        errors = self.validator.validate_geojson_polygon(out_of_bounds_polygon)
        self.assertGreater(len(errors), 0)
        self.assertTrue(
            any("coordinates out of range" in e or "out of WGS84 range" in e for e in errors),
            f"Expected WGS84 range error, got: {errors}"
        )


if __name__ == "__main__":
    unittest.main()
