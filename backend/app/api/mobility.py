"""
backend/app/api/mobility.py
Aggregated mobility and differential temporal analysis endpoints (Features F02, F03, F04, F05, F06).
Strictly applies k-anonymity (Loi ivoirienne n° 2013-450).
"""
from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.services.synthetic_generator import apply_k_anonymity, K_ANONYMITY_THRESHOLD

router = APIRouter(tags=["Mobility"])

SLOTS = [
    ("07h-09h", 1420.0, 580.0, 310.0),   # Morning Commuter Peak
    ("12h-14h", 890.0, 320.0, 305.0),    # Midday Lunch
    ("17h-20h", 1750.0, 720.0, 680.0),   # Evening Peak
    ("02h-04h", 12.0, 4.0, 3.0),         # Late-night sub-threshold (< 15)
]


@router.get("/mobility")
def get_mobility(
    zone_id: Optional[str] = Query(None),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    plage_horaire: Optional[str] = Query(None),
    force_low_volume: bool = Query(False),
) -> List[Dict[str, Any]]:
    target_zone = zone_id or "ci-abidjan-cocody-angre"
    target_date = date_start or datetime.now().strftime("%Y-%m-%d")

    results = []
    for slot_name, vol, in_f, out_f in SLOTS:
        if plage_horaire and plage_horaire != slot_name:
            continue

        raw_vol = 8.0 if force_low_volume else vol
        masked_vol, is_valid_k = apply_k_anonymity(raw_vol)
        results.append({
            "zone_id": target_zone,
            "date": target_date,
            "plage_horaire": slot_name,
            "volume_presence": masked_vol,
            "flux_entrants": in_f if is_valid_k else None,
            "flux_sortants": out_f if is_valid_k else None,
            "seuil_k_anonymat_valide": is_valid_k,
            "est_synthetique": True
        })
    return results


@router.get("/mobility/differential")
def get_differential_analysis(
    zone_id: str = Query(...),
    t1: str = Query(..., description="First period/date"),
    t2: str = Query(..., description="Second period/date"),
) -> Dict[str, Any]:
    vol_t1 = 12500.0
    vol_t2 = 14200.0
    delta = vol_t2 - vol_t1
    pct_change = round((delta / vol_t1) * 100.0, 2)
    return {
        "zone_id": zone_id,
        "periode_1": t1,
        "periode_2": t2,
        "volume_t1": vol_t1,
        "volume_t2": vol_t2,
        "delta_absolu": delta,
        "taux_variation_pct": pct_change
    }
