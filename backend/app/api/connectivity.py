"""
backend/app/api/connectivity.py
Road accessibility and network connectivity metrics (Feature F13).
"""
from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from app.api.data_source import get_zones_dataset

router = APIRouter(tags=["Connectivity"])


@router.get("/connectivity")
def get_connectivity(zone_id: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    zones = get_zones_dataset()
    results = []
    for z in zones:
        if zone_id and z["id"] != zone_id:
            continue
        sc = float(z.get("score_connectivite", 80.0))
        results.append({
            "zone_id": z["id"],
            "score_connectivite": sc,
            "densite_intersections": round(sc * 0.4, 1),
            "proximite_axe_majeur_metres": round(1000.0 - sc * 8.0, 1)
        })
    return results
