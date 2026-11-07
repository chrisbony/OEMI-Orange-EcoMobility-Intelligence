"""
backend/app/models/ipet.py
Model for IPET multicriteria site selection recommendations and explainability.
"""
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ScoreRecommandationIPET(Base):
    __tablename__ = "scores_recommandations_ipet"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id: Mapped[str] = mapped_column(String(36), ForeignKey("zones_geographiques.id", ondelete="CASCADE"), nullable=False)
    secteur_cible: Mapped[str] = mapped_column(String(50), default="SUPERMARCHE", nullable=False)
    score_ipet: Mapped[float] = mapped_column(Float, nullable=False)
    rang_classement: Mapped[int] = mapped_column(Integer, nullable=False)

    # Decision explainability: Top 3 positive factors and limiting factors
    facteurs_positifs: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    facteurs_limitants: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)

    taux_completude: Mapped[float | None] = mapped_column(Float, default=1.0, nullable=True)
    version_modele: Mapped[str] = mapped_column(String(20), default="v1.0", nullable=False)

    calcule_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ORM Relationship
    zone = relationship("ZoneGeographique", back_populates="scores_ipet")

    # Strict mathematical bound [0, 100]
    __table_args__ = (
        CheckConstraint("score_ipet >= 0 AND score_ipet <= 100", name="chk_ipet_score_range"),
    )
