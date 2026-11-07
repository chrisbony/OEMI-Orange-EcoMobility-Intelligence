"""
Application configuration for Orange EcoMobility Intelligence (OEMI).
Loads configuration from environment variables with verified fallbacks.
"""

import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_NEON_DB_URL = (
    "postgresql://neondb_owner:npg_4kz7aAUJPblS@"
    "ep-cold-sea-bdkcgioc.c-8.us-east-2.aws.neon.tech:5432/neondb?sslmode=require"
)

DEFAULT_NEON_DIRECT_URL = (
    "postgresql://neondb_owner:npg_4kz7aAUJPblS@"
    "ep-cold-sea-bdkcgioc.c-8.us-east-2.aws.neon.tech:5432/neondb?sslmode=require"
)


class Settings(BaseSettings):
    """OEMI Application Settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Orange EcoMobility Intelligence"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = Field(default="development")

    # Neon PostgreSQL configuration
    DATABASE_URL: str = Field(default=DEFAULT_NEON_DB_URL)
    DATABASE_DIRECT_URL: str = Field(default=DEFAULT_NEON_DIRECT_URL)
    NEON_API_URL: str = Field(
        default="https://ep-withered-river-bdu4wk58.apirest.c-8.us-east-2.aws.neon.tech/neondb/rest/v1"
    )
    NEON_PROJECT_ID: str = Field(default="young-sky-97422773")

    # Neon pool resilience parameters
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 300
    DB_POOL_PRE_PING: bool = True

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://*.vercel.app",
    ]

    # K-Anonymity privacy threshold per Loi CI n° 2013-450
    K_ANONYMITY_THRESHOLD: int = 15

    # Pilot communes
    PILOT_COMMUNES: List[str] = ["Cocody", "Yopougon", "Marcory"]

    @field_validator("DATABASE_URL", "DATABASE_DIRECT_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str]) -> str:
        if isinstance(v, str):
            if v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+psycopg://", 1)
            elif v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+psycopg://", 1)
            if "sslmode=" not in v:
                separator = "&" if "?" in v else "?"
                v = f"{v}{separator}sslmode=require"
        return v

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Returns database URI formatted for SQLAlchemy with psycopg3 driver."""
        return self.DATABASE_URL


settings = Settings()
