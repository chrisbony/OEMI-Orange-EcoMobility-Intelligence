"""
backend/app/models/demography.py
Demographic profile models aligned with INS RGPH 2021 census data.
"""
import uuid
from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Demographie(Base):
    __tablename__ = "demographie"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("zones_geographiques.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    annee_recensement: Mapped[int] = mapped_column(Integer, default=2021, nullable=False)
    population_totale: Mapped[int] = mapped_column(Integer, nullable=False)
    nombre_menages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    densite_hab_km2: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_donnees: Mapped[str] = mapped_column(String(100), default="INS_RGPH_2021", nullable=False)

    # ORM Relationship
    zone = relationship("ZoneGeographique", back_populates="demographie")
