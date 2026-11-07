"""
SQLAlchemy 2.0 Declarative Models for PostGIS Spatial Database.
Defines all 9 tables conforming to MLD, PostGIS spatial geometries,
GiST indexes, foreign keys, and integrity constraints.
"""

import uuid
from datetime import datetime, date
from typing import Optional, List, Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from geoalchemy2 import Geometry


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


# ----------------------------------------------------------------------------
# 1. zones_geographiques (Referentiel Spatial Communal & Quartiers)
# ----------------------------------------------------------------------------
class ZoneGeographique(Base):
    __tablename__ = "zones_geographiques"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom_commune: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    nom_zone: Mapped[str] = mapped_column(String(150), nullable=False)
    type_zone: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    demographie: Mapped[Optional["Demographie"]] = relationship(
        "Demographie", back_populates="zone", uselist=False, cascade="all, delete-orphan"
    )
    mobilites: Mapped[List["MobiliteAgregee"]] = relationship(
        "MobiliteAgregee", back_populates="zone", cascade="all, delete-orphan"
    )
    infrastructures: Mapped[List["InfrastructureCommerce"]] = relationship(
        "InfrastructureCommerce", back_populates="zone", cascade="all, delete-orphan"
    )
    accessibilite: Mapped[Optional["AccessibiliteRoutiere"]] = relationship(
        "AccessibiliteRoutiere", back_populates="zone", uselist=False, cascade="all, delete-orphan"
    )
    previsions: Mapped[List["PrevisionFrequentation"]] = relationship(
        "PrevisionFrequentation", back_populates="zone", cascade="all, delete-orphan"
    )
    scores_ipet: Mapped[List["ScoreRecommandationIPET"]] = relationship(
        "ScoreRecommandationIPET", back_populates="zone", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ZoneGeographique(id='{self.id}', nom_commune='{self.nom_commune}', nom_zone='{self.nom_zone}')>"


# ----------------------------------------------------------------------------
# 2. mobilite_agregee (Historique & Series Temporelles de Presence)
# ----------------------------------------------------------------------------
class MobiliteAgregee(Base):
    __tablename__ = "mobilite_agregee"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("zones_geographiques.id", ondelete="CASCADE"), nullable=False
    )
    date_observation: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    plage_horaire: Mapped[str] = mapped_column(String(20), nullable=False)
    volume_presence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    flux_entrants: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    flux_sortants: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    est_synthetique: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seuil_k_anonymat_valide: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    zone: Mapped["ZoneGeographique"] = relationship("ZoneGeographique", back_populates="mobilites")

    __table_args__ = (
        UniqueConstraint("zone_id", "date_observation", "plage_horaire", name="uq_mobilite_zone_date_plage"),
        Index("idx_mobilite_zone_date_plage", "zone_id", "date_observation", "plage_horaire"),
    )

    def __repr__(self) -> str:
        return (
            f"<MobiliteAgregee(zone_id='{self.zone_id}', date='{self.date_observation}', "
            f"plage='{self.plage_horaire}', volume={self.volume_presence})>"
        )


# ----------------------------------------------------------------------------
# 3. demographie (Donnees INS / RGPH 2021)
# ----------------------------------------------------------------------------
class Demographie(Base):
    __tablename__ = "demographie"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("zones_geographiques.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    annee_recensement: Mapped[int] = mapped_column(Integer, default=2021, nullable=False)
    population_totale: Mapped[int] = mapped_column(Integer, nullable=False)
    nombre_menages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    densite_hab_km2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_donnees: Mapped[str] = mapped_column(String(100), default="INS_RGPH_2021", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    zone: Mapped["ZoneGeographique"] = relationship("ZoneGeographique", back_populates="demographie")

    def __repr__(self) -> str:
        return f"<Demographie(zone_id='{self.zone_id}', population={self.population_totale})>"


# ----------------------------------------------------------------------------
# 4. infrastructures_commerces (Points d'Interet Commerciaux OSM)
# ----------------------------------------------------------------------------
class InfrastructureCommerce(Base):
    __tablename__ = "infrastructures_commerces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("zones_geographiques.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type_activite: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    nom_enseigne: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    geom_point = Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=False)
    source_osm: Mapped[str] = mapped_column(String(100), default="OpenStreetMap", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    zone: Mapped["ZoneGeographique"] = relationship("ZoneGeographique", back_populates="infrastructures")

    def __repr__(self) -> str:
        return f"<InfrastructureCommerce(id='{self.id}', enseigne='{self.nom_enseigne}', type='{self.type_activite}')>"


# ----------------------------------------------------------------------------
# 5. accessibilite_routiere (Connectivite & Transports)
# ----------------------------------------------------------------------------
class AccessibiliteRoutiere(Base):
    __tablename__ = "accessibilite_routiere"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("zones_geographiques.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    score_connectivite: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nombre_arrets_transport: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    densite_carrefours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    zone: Mapped["ZoneGeographique"] = relationship("ZoneGeographique", back_populates="accessibilite")

    __table_args__ = (
        CheckConstraint("score_connectivite BETWEEN 0 AND 100", name="chk_score_connectivite_range"),
    )

    def __repr__(self) -> str:
        return f"<AccessibiliteRoutiere(zone_id='{self.zone_id}', score={self.score_connectivite})>"


# ----------------------------------------------------------------------------
# 6. previsions_frequentation (Resultats Modeles IA - D-7, Prophet, XGBoost)
# ----------------------------------------------------------------------------
class PrevisionFrequentation(Base):
    __tablename__ = "previsions_frequentation"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("zones_geographiques.id", ondelete="CASCADE"), nullable=False
    )
    date_horizon: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valeur_estimee: Mapped[float] = mapped_column(Float, nullable=False)
    borne_inferieure: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    borne_superieure: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    modele_utilise: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    metrique_wape: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    zone: Mapped["ZoneGeographique"] = relationship("ZoneGeographique", back_populates="previsions")

    __table_args__ = (
        CheckConstraint("modele_utilise IN ('NAIVE_D7', 'PROPHET', 'XGBOOST')", name="chk_modele_utilise"),
        Index("idx_previsions_zone_modele_date", "zone_id", "modele_utilise", "date_horizon"),
    )

    def __repr__(self) -> str:
        return f"<PrevisionFrequentation(zone_id='{self.zone_id}', modele='{self.modele_utilise}', est={self.valeur_estimee})>"


# ----------------------------------------------------------------------------
# 7. scores_recommandations_ipet (Moteur Decisionnel IPET)
# ----------------------------------------------------------------------------
class ScoreRecommandationIPET(Base):
    __tablename__ = "scores_recommandations_ipet"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("zones_geographiques.id", ondelete="CASCADE"), nullable=False
    )
    secteur_cible: Mapped[str] = mapped_column(String(50), default="SUPERMARCHE", nullable=False)
    score_ipet: Mapped[float] = mapped_column(Float, nullable=False)
    rang_classement: Mapped[int] = mapped_column(Integer, nullable=False)
    facteurs_positifs = Column(JSONB().with_variant(JSON(), "sqlite"), default=list)
    facteurs_limitants = Column(JSONB().with_variant(JSON(), "sqlite"), default=list)
    taux_completude: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    version_modele: Mapped[str] = mapped_column(String(20), default="v1.0", nullable=False)
    calcule_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    zone: Mapped["ZoneGeographique"] = relationship("ZoneGeographique", back_populates="scores_ipet")

    __table_args__ = (
        CheckConstraint("score_ipet BETWEEN 0 AND 100", name="chk_score_ipet_range"),
        CheckConstraint("taux_completude BETWEEN 0 AND 1", name="chk_taux_completude_range"),
        Index("idx_ipet_zone_secteur", "zone_id", "secteur_cible"),
        Index("idx_ipet_score", "score_ipet"),
        Index("idx_ipet_rang", "rang_classement"),
    )

    def __repr__(self) -> str:
        return f"<ScoreRecommandationIPET(zone_id='{self.zone_id}', score={self.score_ipet}, rang={self.rang_classement})>"


# ----------------------------------------------------------------------------
# 8. utilisateurs (Authentification & Roles RBAC)
# ----------------------------------------------------------------------------
class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    journaux_audit: Mapped[List["JournalAudit"]] = relationship("JournalAudit", back_populates="utilisateur")

    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'ANALYSTE', 'METIER')", name="chk_user_role"),
        Index("uq_utilisateurs_email", "email", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Utilisateur(id='{self.id}', email='{self.email}', role='{self.role}')>"


# ----------------------------------------------------------------------------
# 9. journaux_audit (Tracabilite & Securite)
# ----------------------------------------------------------------------------
class JournalAudit(Base):
    __tablename__ = "journaux_audit"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    utilisateur_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    zone_concernee: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    horodatage: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    parametres_filtres = Column(JSONB().with_variant(JSON(), "sqlite"), default=dict)

    utilisateur: Mapped[Optional["Utilisateur"]] = relationship("Utilisateur", back_populates="journaux_audit")

    __table_args__ = (
        CheckConstraint(
            "action_type IN ('CONSULTATION', 'EXPORT_PDF', 'EXPORT_EXCEL', 'CALCUL_IPET', 'LOGIN', 'LOGOUT')",
            name="chk_audit_action_type"
        ),
    )

    def __repr__(self) -> str:
        return f"<JournalAudit(action='{self.action_type}', user='{self.utilisateur_id}', timestamp='{self.horodatage}')>"
