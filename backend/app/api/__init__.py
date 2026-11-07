"""
backend/app/api/__init__.py
Modular API routers package.
"""
from app.api.health import router as health_router
from app.api.zones import router as zones_router
from app.api.mobility import router as mobility_router
from app.api.predictions import router as predictions_router
from app.api.demography import router as demography_router
from app.api.pois import router as pois_router
from app.api.connectivity import router as connectivity_router
from app.api.clusters import router as clusters_router
from app.api.ipet import router as ipet_router
from app.api.reports import router as reports_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.probes import router as probes_router

__all__ = [
    "health_router",
    "zones_router",
    "mobility_router",
    "predictions_router",
    "demography_router",
    "pois_router",
    "connectivity_router",
    "clusters_router",
    "ipet_router",
    "reports_router",
    "audit_router",
    "auth_router",
    "probes_router",
]
