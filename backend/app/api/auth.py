"""
backend/app/api/auth.py
Authentication and Role-Based Access Control (RBAC) (Feature F27).
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
import time

router = APIRouter(tags=["Auth"])


class AuthRequest(BaseModel):
    username: str
    role: str = "ANALYSTE"


PERMISSIONS_BY_ROLE: Dict[str, List[str]] = {
    "ADMIN": ["read", "write", "simulate", "audit_read"],
    "ANALYSTE": ["read", "recalculate_ipet", "export_pdf", "export_excel"],
    "METIER": ["read", "view_rankings"]
}


@router.post("/auth/token")
def authenticate(req: AuthRequest) -> Dict[str, Any]:
    role = req.role.upper()
    if role not in PERMISSIONS_BY_ROLE:
        raise HTTPException(
            status_code=400,
            detail=f"Rôle invalide: {req.role}. Rôles autorisés: ADMIN, ANALYSTE, METIER."
        )

    token = f"jwt_{role.lower()}_{req.username}_{int(time.time())}"
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": role,
        "permissions": PERMISSIONS_BY_ROLE[role]
    }
