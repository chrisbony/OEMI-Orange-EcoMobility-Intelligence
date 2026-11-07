"""
backend/app/api/ipet.py
Indice de Potentiel Économique Territorial (IPET) multicriteria scoring engine (Features F15, F16, F17, F18, F19).
"""
from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.api.data_source import get_zones_dataset

router = APIRouter(tags=["IPET"])


class IPETCalculationRequest(BaseModel):
    secteur: str = Field(default="SUPERMARCHE")
    weights: Optional[Dict[str, float]] = None


def compute_ipet_for_zones(
    secteur: str = "SUPERMARCHE",
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    w = weights or {
        "frequentation": 0.30,
        "demographie": 0.25,
        "accessibilite": 0.20,
        "dynamique": 0.15,
        "concurrence": 0.10
    }

    w_sum = round(sum(w.values()), 4)
    if abs(w_sum - 1.0) > 0.001 or any(val < 0.0 for val in w.values()):
        raise HTTPException(
            status_code=400,
            detail=f"Les poids doivent totaliser 1.0 (100%) sans valeurs négatives. Somme reçue: {w_sum}"
        )

    zones = get_zones_dataset()
    recs = []

    for z in zones:
        pop = float(z.get("population", 100000))
        dens = float(z.get("densite", 8000.0))
        conn = float(z.get("score_connectivite", 75.0))
        dyn = float(z.get("dynamique", 65.0 + (hash(z["id"]) % 30)))
        nb_comp = int(z.get("nb_commerces_concurrents", 4))

        c_freq = min(100.0, max(0.0, pop / 2500.0))
        c_demo = min(100.0, max(0.0, dens / 180.0))
        c_acc = min(100.0, max(0.0, conn))
        c_dyn = min(100.0, max(0.0, dyn))
        c_comp = max(0.0, min(100.0, 100.0 - (nb_comp * 10.0)))

        raw_ipet = (
            w["frequentation"] * c_freq +
            w["demographie"] * c_demo +
            w["accessibilite"] * c_acc +
            w["dynamique"] * c_dyn +
            w["concurrence"] * c_comp
        )
        clamped_ipet = round(min(100.0, max(0.0, raw_ipet)), 1)

        # Top 3 positive factors
        contributions = [
            ("Fréquentation pendulaire", round(w["frequentation"] * c_freq, 1)),
            ("Bassin démographique", round(w["demographie"] * c_demo, 1)),
            ("Connectivité routière", round(w["accessibilite"] * c_acc, 1)),
            ("Dynamique de croissance", round(w["dynamique"] * c_dyn, 1)),
            ("Faible saturation concurrentielle", round(w["concurrence"] * c_comp, 1))
        ]
        contributions.sort(key=lambda x: x[1], reverse=True)
        facteurs_positifs = [
            {"facteur": name, "contribution": contrib}
            for name, contrib in contributions[:3]
        ]

        # Limiting factors
        limiting = []
        if nb_comp >= 5:
            limiting.append({"facteur": "Pression concurrentielle élevée", "impact": round(-(nb_comp * 2.0), 1)})
        if c_acc < 70.0:
            limiting.append({"facteur": "Enclavement ou connectivité restreinte", "impact": -5.0})

        recs.append({
            "zone_id": z["id"],
            "nom_zone": z["nom_zone"],
            "nom_commune": z["nom_commune"],
            "score_ipet": clamped_ipet,
            "facteurs_positifs": facteurs_positifs,
            "facteurs_limitants": limiting,
            "taux_completude": 0.95
        })

    recs.sort(key=lambda r: (-r["score_ipet"], r["zone_id"]))
    for rank_idx, r in enumerate(recs, start=1):
        r["rang"] = rank_idx

    return {
        "secteur": secteur,
        "poids_utilises": w,
        "recommendations": recs
    }


@router.get("/ipet")
def get_ipet(
    secteur: str = Query("SUPERMARCHE"),
    frequentation: Optional[float] = Query(None),
    demographie: Optional[float] = Query(None),
    accessibilite: Optional[float] = Query(None),
    dynamique: Optional[float] = Query(None),
    concurrence: Optional[float] = Query(None),
) -> Dict[str, Any]:
    weights = None
    if frequentation is not None and demographie is not None:
        weights = {
            "frequentation": frequentation,
            "demographie": demographie,
            "accessibilite": accessibilite or 0.20,
            "dynamique": dynamique or 0.15,
            "concurrence": concurrence or 0.10
        }
    return compute_ipet_for_zones(secteur=secteur, weights=weights)


@router.post("/ipet")
def post_ipet(body: IPETCalculationRequest) -> Dict[str, Any]:
    return compute_ipet_for_zones(secteur=body.secteur, weights=body.weights)
