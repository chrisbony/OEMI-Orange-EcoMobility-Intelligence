"""
backend/app/api/demography.py
Demographic data from INS RGPH 2021 (Feature F11).
"""
from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from app.api.data_source import get_zones_dataset

router = APIRouter(tags=["Demography"])


@router.get("/demography")
def get_demography(
    zone_id: Optional[str] = Query(None),
    commune: Optional[str] = Query(None)
) -> List[Dict[str, Any]]:
    zones = get_zones_dataset(commune=commune)
    results = []
    for z in zones:
        if zone_id and z["id"] != zone_id:
            continue
        pop = z.get("population", 100000)
        results.append({
            "zone_id": z["id"],
            "nom_commune": z["nom_commune"],
            "nom_zone": z["nom_zone"],
            "population_totale": pop,
            "nombre_menages": int(pop / 4.5),
            "densite_hab_km2": z.get("densite", 8000.0),
            "source": "INS_RGPH_2021"
        })
    return results
