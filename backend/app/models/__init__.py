"""
backend/app/models/__init__.py
OEMI PostGIS and relational models package.
Exports all 9 tables conforming to MLD.
"""
from app.db.base import Base
from app.models.zone import ZoneGeographique
from app.models.mobility import MobiliteAgregee
from app.models.demography import Demographie
from app.models.infrastructure import InfrastructureCommerce, AccessibiliteRoutiere
from app.models.prediction import PrevisionFrequentation
from app.models.ipet import ScoreRecommandationIPET
from app.models.audit import Utilisateur, JournalAudit

__all__ = [
    "Base",
    "ZoneGeographique",
    "MobiliteAgregee",
    "Demographie",
    "InfrastructureCommerce",
    "AccessibiliteRoutiere",
    "PrevisionFrequentation",
    "ScoreRecommandationIPET",
    "Utilisateur",
    "JournalAudit",
]
