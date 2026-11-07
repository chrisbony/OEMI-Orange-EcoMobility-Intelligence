"""
backend/app/services/synthetic_generator.py
Spatially and temporally constrained synthetic mobility generator for Abidjan.
Conforms strictly to:
- Fallback strategy: Cahier des Charges §13.1 & Technical Specification §4.2
- Privacy: Ivorian Law n° 2013-450 on personal data protection (k-anonymity k >= 15)
- Traceability: est_synthetique = True
- Zero PII guarantee: aggregate statistical volumes only
"""

import uuid
import datetime
import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

K_ANONYMITY_THRESHOLD: float = 15.0

STANDARD_TIME_SLICES: List[str] = [
    "08h-10h",
    "10h-12h",
    "12h-14h",
    "14h-16h",
    "16h-18h",
    "18h-20h",
    "20h-22h",
    "22h-08h",
]


def apply_k_anonymity(volume_estime: Optional[float]) -> Tuple[Optional[float], bool]:
    """
    Applies strict k-anonymity masking according to Ivorian Law n° 2013-450.
    Returns (masked_volume, is_valid_k_anonymity).
    - If volume_estime >= 15.0: (round(volume_estime, 1), True)
    - If volume_estime < 15.0 or None: (None, False)
    """
    if volume_estime is None or volume_estime < K_ANONYMITY_THRESHOLD:
        return None, False
    return round(float(volume_estime), 1), True


# Territorial reference profiles with alias support
PRIMARY_ZONE_PROFILES: Dict[str, Dict[str, Any]] = {
    "ci-abidjan-cocody-angre": {
        "nom_commune": "Cocody",
        "nom_zone": "Angré 7e Tranche",
        "typologie": "RESIDENTIEL",
        "base_presence": 8500.0,
    },
    "ci-abidjan-cocody-deux-plateaux": {
        "nom_commune": "Cocody",
        "nom_zone": "Deux Plateaux Vallons",
        "typologie": "MIXTE",
        "base_presence": 6200.0,
    },
    "ci-abidjan-cocody-palmeraie": {
        "nom_commune": "Cocody",
        "nom_zone": "Riviera Palmeraie",
        "typologie": "RESIDENTIEL",
        "base_presence": 7800.0,
    },
    "ci-abidjan-yopougon-niangon-nord": {
        "nom_commune": "Yopougon",
        "nom_zone": "Niangon Nord",
        "typologie": "RESIDENTIEL",
        "base_presence": 11500.0,
    },
    "ci-abidjan-yopougon-toit-rouge": {
        "nom_commune": "Yopougon",
        "nom_zone": "Toit Rouge",
        "typologie": "MIXTE",
        "base_presence": 6900.0,
    },
    "ci-abidjan-yopougon-maroc": {
        "nom_commune": "Yopougon",
        "nom_zone": "Maroc",
        "typologie": "RESIDENTIEL",
        "base_presence": 8200.0,
    },
    "ci-abidjan-marcory-zone4c": {
        "nom_commune": "Marcory",
        "nom_zone": "Zone 4C",
        "typologie": "COMMERCIAL",
        "base_presence": 4200.0,
    },
    "ci-abidjan-marcory-bietry": {
        "nom_commune": "Marcory",
        "nom_zone": "Biétry",
        "typologie": "COMMERCIAL",
        "base_presence": 4800.0,
    },
    "ci-abidjan-marcory-anoumabo": {
        "nom_commune": "Marcory",
        "nom_zone": "Anoumabo",
        "typologie": "MIXTE",
        "base_presence": 5400.0,
    },
}

# Alias mapping ensuring both canonical and abbreviated IDs resolve seamlessly
ZONE_ALIASES: Dict[str, str] = {
    "ci-abidjan-cocody-2plateaux": "ci-abidjan-cocody-deux-plateaux",
    "ci-abidjan-cocody-deuxplateaux": "ci-abidjan-cocody-deux-plateaux",
    "ci-abidjan-cocody-riviera": "ci-abidjan-cocody-palmeraie",
    "ci-abidjan-yopougon-niangon": "ci-abidjan-yopougon-niangon-nord",
    "ci-abidjan-yopougon-toitsrouges": "ci-abidjan-yopougon-toit-rouge",
    "ci-abidjan-yopougon-siporex": "ci-abidjan-yopougon-toit-rouge",
    "ci-abidjan-marcory-zone4": "ci-abidjan-marcory-zone4c",
}

# Unified zone lookup
ZONE_PROFILES: Dict[str, Dict[str, Any]] = {}
for _k, _v in PRIMARY_ZONE_PROFILES.items():
    ZONE_PROFILES[_k] = _v
for _alias, _target in ZONE_ALIASES.items():
    if _target in PRIMARY_ZONE_PROFILES:
        ZONE_PROFILES[_alias] = PRIMARY_ZONE_PROFILES[_target]

# Diurnal presence coefficient matrices
DIURNAL_COEFFICIENTS: Dict[str, Dict[str, Dict[str, float]]] = {
    "WEEKDAY": {
        "RESIDENTIEL": {
            "22h-08h": 1.00, "08h-10h": 0.55, "10h-12h": 0.45,
            "12h-14h": 0.50, "14h-16h": 0.45, "16h-18h": 0.70,
            "18h-20h": 0.95, "20h-22h": 1.05
        },
        "COMMERCIAL": {
            "22h-08h": 0.25, "08h-10h": 1.60, "10h-12h": 1.80,
            "12h-14h": 1.95, "14h-16h": 1.75, "16h-18h": 1.40,
            "18h-20h": 1.10, "20h-22h": 0.80
        },
        "MIXTE": {
            "22h-08h": 0.60, "08h-10h": 1.10, "10h-12h": 1.15,
            "12h-14h": 1.35, "14h-16h": 1.10, "16h-18h": 1.20,
            "18h-20h": 1.25, "20h-22h": 0.90
        },
    },
    "SATURDAY": {
        "RESIDENTIEL": {
            "22h-08h": 1.00, "08h-10h": 0.90, "10h-12h": 0.80,
            "12h-14h": 0.85, "14h-16h": 0.75, "16h-18h": 0.70,
            "18h-20h": 0.75, "20h-22h": 0.85
        },
        "COMMERCIAL": {
            "22h-08h": 0.30, "08h-10h": 0.80, "10h-12h": 1.50,
            "12h-14h": 1.60, "14h-16h": 1.80, "16h-18h": 2.20,
            "18h-20h": 2.30, "20h-22h": 1.90
        },
        "MIXTE": {
            "22h-08h": 0.65, "08h-10h": 0.85, "10h-12h": 1.20,
            "12h-14h": 1.25, "14h-16h": 1.30, "16h-18h": 1.45,
            "18h-20h": 1.40, "20h-22h": 1.10
        },
    },
    "SUNDAY": {
        "RESIDENTIEL": {
            "22h-08h": 1.00, "08h-10h": 0.85, "10h-12h": 0.80,
            "12h-14h": 0.95, "14h-16h": 0.90, "16h-18h": 0.85,
            "18h-20h": 0.95, "20h-22h": 1.00
        },
        "COMMERCIAL": {
            "22h-08h": 0.25, "08h-10h": 0.50, "10h-12h": 0.70,
            "12h-14h": 1.10, "14h-16h": 0.90, "16h-18h": 1.00,
            "18h-20h": 0.65, "20h-22h": 0.40
        },
        "MIXTE": {
            "22h-08h": 0.60, "08h-10h": 0.75, "10h-12h": 0.80,
            "12h-14h": 1.05, "14h-16h": 0.95, "16h-18h": 0.95,
            "18h-20h": 0.85, "20h-22h": 0.70
        },
    },
}


@dataclass
class SyntheticMobilityRecord:
    id: str
    zone_id: str
    date_observation: datetime.date
    plage_horaire: str
    volume_presence: Optional[float]
    flux_entrants: Optional[float]
    flux_sortants: Optional[float]
    est_synthetique: bool
    seuil_k_anonymat_valide: bool


class SyntheticMobilityGenerator:
    """Realistic commuter flow and presence generator for Abidjan pilot communes."""

    def __init__(self, seed: Optional[int] = 42):
        self.seed = seed
        if seed is not None:
            self.rng = random.Random(seed)
        else:
            self.rng = random.Random()

    def _get_day_type(self, dt: datetime.date) -> str:
        weekday = dt.weekday()
        if weekday == 5:
            return "SATURDAY"
        elif weekday == 6:
            return "SUNDAY"
        return "WEEKDAY"

    def generate_single_record(
        self,
        zone_id: str,
        date_obs: datetime.date,
        slice_label: str,
        force_low_volume: bool = False
    ) -> SyntheticMobilityRecord:
        """Generates a single synthetic mobility record with strict k-anonymity validation."""
        profile = ZONE_PROFILES.get(zone_id)
        if not profile:
            raise ValueError(f"Unknown zone ID: {zone_id}")

        typology = profile["typologie"]
        base_presence = profile["base_presence"]
        day_type = self._get_day_type(date_obs)

        coef = DIURNAL_COEFFICIENTS[day_type][typology].get(slice_label, 1.0)

        # Realistic Gaussian noise (+/- 4%)
        noise = self.rng.gauss(1.0, 0.04)
        raw_volume = base_presence * coef * noise

        if force_low_volume:
            raw_volume = self.rng.uniform(1.0, 14.0)

        # Inflow / Outflow dynamics
        if day_type == "WEEKDAY":
            if slice_label == "08h-10h":
                if typology == "RESIDENTIEL":
                    raw_outflow = raw_volume * 0.35 * self.rng.uniform(0.95, 1.05)
                    raw_inflow = raw_volume * 0.05 * self.rng.uniform(0.95, 1.05)
                elif typology == "COMMERCIAL":
                    raw_inflow = raw_volume * 0.45 * self.rng.uniform(0.95, 1.05)
                    raw_outflow = raw_volume * 0.06 * self.rng.uniform(0.95, 1.05)
                else:  # MIXTE
                    raw_inflow = raw_volume * 0.20 * self.rng.uniform(0.95, 1.05)
                    raw_outflow = raw_volume * 0.15 * self.rng.uniform(0.95, 1.05)
            elif slice_label in ("16h-18h", "18h-20h"):
                if typology == "RESIDENTIEL":
                    raw_inflow = raw_volume * 0.30 * self.rng.uniform(0.95, 1.05)
                    raw_outflow = raw_volume * 0.08 * self.rng.uniform(0.95, 1.05)
                elif typology == "COMMERCIAL":
                    raw_outflow = raw_volume * 0.38 * self.rng.uniform(0.95, 1.05)
                    raw_inflow = raw_volume * 0.15 * self.rng.uniform(0.95, 1.05)
                else:  # MIXTE
                    raw_inflow = raw_volume * 0.22 * self.rng.uniform(0.95, 1.05)
                    raw_outflow = raw_volume * 0.20 * self.rng.uniform(0.95, 1.05)
            else:
                raw_inflow = raw_volume * 0.10 * self.rng.uniform(0.85, 1.15)
                raw_outflow = raw_volume * 0.10 * self.rng.uniform(0.85, 1.15)
        else:
            # Weekend
            raw_inflow = raw_volume * 0.12 * self.rng.uniform(0.85, 1.15)
            raw_outflow = raw_volume * 0.12 * self.rng.uniform(0.85, 1.15)

        # Enforce k-anonymity masking (k >= 15)
        vol_masked, is_valid_k = apply_k_anonymity(raw_volume)
        if not is_valid_k:
            volume_presence = None
            flux_entrants = None
            flux_sortants = None
        else:
            volume_presence = vol_masked
            flux_entrants = round(raw_inflow, 1)
            flux_sortants = round(raw_outflow, 1)

        return SyntheticMobilityRecord(
            id=str(uuid.uuid4()),
            zone_id=zone_id,
            date_observation=date_obs,
            plage_horaire=slice_label,
            volume_presence=volume_presence,
            flux_entrants=flux_entrants,
            flux_sortants=flux_sortants,
            est_synthetique=True,
            seuil_k_anonymat_valide=is_valid_k,
        )

    def generate_range(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        zone_ids: Optional[List[str]] = None,
        inject_low_volume_samples: bool = True
    ) -> List[SyntheticMobilityRecord]:
        """Generates time series records across the requested date window and zones."""
        targets = zone_ids or list(PRIMARY_ZONE_PROFILES.keys())
        records = []
        delta = (end_date - start_date).days + 1

        for day_offset in range(delta):
            current_date = start_date + datetime.timedelta(days=day_offset)
            for z in targets:
                for sl in STANDARD_TIME_SLICES:
                    is_low = False
                    if inject_low_volume_samples and day_offset == 0 and z == targets[0] and sl == "22h-08h":
                        is_low = True

                    rec = self.generate_single_record(
                        zone_id=z,
                        date_obs=current_date,
                        slice_label=sl,
                        force_low_volume=is_low
                    )
                    records.append(rec)

        return records
