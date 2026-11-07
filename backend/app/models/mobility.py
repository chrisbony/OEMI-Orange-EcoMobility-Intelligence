"""
backend/app/models/mobility.py
Aggregated mobility time-series with k-anonymity compliance (Loi CI n° 2013-450).
"""
import uuid
from datetime import date
from sqlalchemy import String, Date, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class MobiliteAgregee(Base):
    __tablename__ = "mobilite_agregee"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id: Mapped[str] = mapped_column(String(36), ForeignKey("zones_geographiques.id", ondelete="CASCADE"), nullable=False)
    date_observation: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    plage_horaire: Mapped[str] = mapped_column(String(20), nullable=False)

    # Mobility indicators
    volume_presence: Mapped[float | None] = mapped_column(Float, nullable=True)
    flux_entrants: Mapped[float | None] = mapped_column(Float, nullable=True)
    flux_sortants: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Governance & Privacy
    est_synthetique: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seuil_k_anonymat_valide: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ORM Relationship
    zone = relationship("ZoneGeographique", back_populates="mobilite_records")

    # Composite index for efficient time-series queries
    __table_args__ = (
        Index("idx_mobilite_zone_date_plage", "zone_id", "date_observation", "plage_horaire"),
    )
