"""
backend/app/api/zones.py
Geographic zones GeoJSON FeatureCollection endpoint (Feature F01).
"""
from fastapi import APIRouter, Query
from typing import Optional, Dict, Any
from app.api.data_source import get_zones_dataset

router = APIRouter(tags=["Zones"])


@router.get("/zones")
def get_zones(commune: Optional[str] = Query(None, description="Filter by commune name")) -> Dict[str, Any]:
    zones = get_zones_dataset(commune=commune)
    features = []
    for z in zones:
        features.append({
            "type": "Feature",
            "id": z["id"],
            "geometry": z["geom"],
            "properties": {
                "nom_commune": z["nom_commune"],
                "nom_zone": z["nom_zone"],
                "type_zone": z["type_zone"],
                "population": z.get("population", 100000),
                "densite": z.get("densite", 8000.0),
                "score_connectivite": z.get("score_connectivite", 80.0),
                "score_ipet": round(70.0 + (hash(z["id"]) % 25), 1)
            }
        })
    return {
        "type": "FeatureCollection",
        "features": features
    }
