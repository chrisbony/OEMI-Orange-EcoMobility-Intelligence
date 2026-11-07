"""
backend/app/models/infrastructure.py
PostGIS models for OpenStreetMap commercial POIs and road accessibility scores.
"""
import uuid
from sqlalchemy import String, Integer, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.db.base import Base


class InfrastructureCommerce(Base):
    __tablename__ = "infrastructures_commerces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id: Mapped[str] = mapped_column(String(36), ForeignKey("zones_geographiques.id", ondelete="CASCADE"), nullable=False)
    type_activite: Mapped[str] = mapped_column(String(100), nullable=False)
    nom_enseigne: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Point spatial PostGIS EPSG:4326 with automatic GiST index
    geom_point: Mapped[Geometry] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False
    )
    source_osm: Mapped[str] = mapped_column(String(100), default="OpenStreetMap", nullable=False)

    # ORM Relationship
    zone = relationship("ZoneGeographique", back_populates="infrastructures")


class AccessibiliteRoutiere(Base):
    __tablename__ = "accessibilite_routiere"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("zones_geographiques.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    score_connectivite: Mapped[float] = mapped_column(Float, nullable=False)
    nombre_arrets_transport: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    densite_carrefours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ORM Relationship
    zone = relationship("ZoneGeographique", back_populates="accessibilite")

    # Strict mathematical bound [0, 100]
    __table_args__ = (
        CheckConstraint("score_connectivite >= 0 AND score_connectivite <= 100", name="chk_connectivite_range"),
    )
