"""
backend/app/api/pois.py
Commercial Points of Interest (supermarkets, convenience stores) (Feature F12).
"""
from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from app.api.data_source import get_pois_dataset

router = APIRouter(tags=["POIs"])


@router.get("/pois")
def get_pois(
    commune: Optional[str] = Query(None),
    type_activite: Optional[str] = Query(None)
) -> List[Dict[str, Any]]:
    return get_pois_dataset(commune=commune, type_activite=type_activite)
