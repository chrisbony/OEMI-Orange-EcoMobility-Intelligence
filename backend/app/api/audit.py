"""
backend/app/api/audit.py
Security audit trails and access logging (Feature F26).
"""
from fastapi import APIRouter
from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(tags=["Audit"])

_IN_MEMORY_LOGS: List[Dict[str, Any]] = []


class AuditLogEntry(BaseModel):
    action: str
    user_id: str
    details: Dict[str, Any] = {}


@router.post("/audit/log")
def create_audit_log(entry: AuditLogEntry) -> Dict[str, Any]:
    record = {
        "id": len(_IN_MEMORY_LOGS) + 1,
        "action": entry.action,
        "user_id": entry.user_id,
        "timestamp": datetime.now().isoformat(),
        "details": entry.details
    }
    _IN_MEMORY_LOGS.append(record)
    return record


@router.get("/audit/logs")
def list_audit_logs() -> List[Dict[str, Any]]:
    return list(_IN_MEMORY_LOGS)
