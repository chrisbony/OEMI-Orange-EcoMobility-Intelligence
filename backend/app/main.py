"""
backend/app/main.py
Main FastAPI application entrypoint for Orange EcoMobility Intelligence (OEMI).
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import (
    health_router,
    zones_router,
    mobility_router,
    predictions_router,
    demography_router,
    pois_router,
    connectivity_router,
    clusters_router,
    ipet_router,
    reports_router,
    audit_router,
    auth_router,
    probes_router,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("oemi")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Plateforme d'intelligence territoriale et aide à la décision pour l'implantation commerciale à Abidjan.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Enable CORS for Next.js frontend and local tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root probe
@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "operational",
        "docs": "/docs",
        "communes": settings.PILOT_COMMUNES
    }

# Register all modular routers under /api
app.include_router(health_router, prefix="/api")
app.include_router(zones_router, prefix="/api")
app.include_router(mobility_router, prefix="/api")
app.include_router(predictions_router, prefix="/api")
app.include_router(demography_router, prefix="/api")
app.include_router(pois_router, prefix="/api")
app.include_router(connectivity_router, prefix="/api")
app.include_router(clusters_router, prefix="/api")
app.include_router(ipet_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(probes_router, prefix="/api")

# Also register health at root
app.include_router(health_router)
