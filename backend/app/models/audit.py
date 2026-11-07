"""
backend/app/models/audit.py
RBAC user model and immutable audit logging models.
"""
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ORM Relationship
    journaux_audit = relationship("JournalAudit", back_populates="utilisateur")

    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'ANALYSTE', 'METIER')", name="chk_user_role"),
    )


class JournalAudit(Base):
    __tablename__ = "journaux_audit"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    utilisateur_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("utilisateurs.id", ondelete="SET NULL"),
        nullable=True
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    zone_concernee: Mapped[str | None] = mapped_column(String(150), nullable=True)

    horodatage: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    parametres_filtres: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # ORM Relationship
    utilisateur = relationship("Utilisateur", back_populates="journaux_audit")

    __table_args__ = (
        CheckConstraint(
            "action_type IN ('CONSULTATION', 'EXPORT_PDF', 'EXPORT_EXCEL', 'CALCUL_IPET', 'LOGIN', 'LOGOUT')",
            name="chk_action_type"
        ),
    )
