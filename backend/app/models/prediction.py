"""
backend/app/models/prediction.py
Model for time-series forecasting horizons (Naïve D-7, Prophet, XGBoost).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PrevisionFrequentation(Base):
    __tablename__ = "previsions_frequentation"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id: Mapped[str] = mapped_column(String(36), ForeignKey("zones_geographiques.id", ondelete="CASCADE"), nullable=False)
    date_horizon: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    valeur_estimee: Mapped[float] = mapped_column(Float, nullable=False)
    borne_inferieure: Mapped[float | None] = mapped_column(Float, nullable=True)
    borne_superieure: Mapped[float | None] = mapped_column(Float, nullable=True)
    modele_utilise: Mapped[str] = mapped_column(String(50), nullable=False)
    metrique_wape: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ORM Relationship
    zone = relationship("ZoneGeographique", back_populates="previsions")

    __table_args__ = (
        CheckConstraint("modele_utilise IN ('NAIVE_D7', 'PROPHET', 'XGBOOST')", name="chk_modele_type"),
    )
