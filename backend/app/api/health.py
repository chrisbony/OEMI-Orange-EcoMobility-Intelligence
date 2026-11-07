"""
backend/app/api/health.py
Health check and readiness endpoints.
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Orange EcoMobility Intelligence",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
