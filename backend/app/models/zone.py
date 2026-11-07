"""
backend/app/models/zone.py
PostGIS model for geographic zones in Abidjan (EPSG:4326).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.db.base import Base


class ZoneGeographique(Base):
    __tablename__ = "zones_geographiques"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom_commune: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    nom_zone: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    type_zone: Mapped[str] = mapped_column(String(50), nullable=False)

    # Geometry Polygon in WGS84 EPSG:4326 with automatic GiST index
    geom: Mapped[Geometry] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ORM Relationships
    mobilite_records = relationship("MobiliteAgregee", back_populates="zone", cascade="all, delete-orphan")
    demographie = relationship("Demographie", back_populates="zone", uselist=False, cascade="all, delete-orphan")
    infrastructures = relationship("InfrastructureCommerce", back_populates="zone", cascade="all, delete-orphan")
    accessibilite = relationship("AccessibiliteRoutiere", back_populates="zone", uselist=False, cascade="all, delete-orphan")
    previsions = relationship("PrevisionFrequentation", back_populates="zone", cascade="all, delete-orphan")
    scores_ipet = relationship("ScoreRecommandationIPET", back_populates="zone", cascade="all, delete-orphan")
