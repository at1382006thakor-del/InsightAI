from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import os
import json

from ..database.connection import get_db
from ..database.models import User
from ..services.auth_service import get_current_admin

router = APIRouter(prefix="/settings", tags=["System Configuration Settings"])

SETTINGS_FILE = "settings.json"

def load_local_settings() -> Dict[str, Any]:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"gemini_api_key": "", "database_type": "sqlite"}

def save_local_settings(settings: Dict[str, Any]) -> None:
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist settings: {str(e)}"
        )

@router.get("")
def get_system_settings(
    current_user: User = Depends(get_current_admin)
):
    settings = load_local_settings()
    has_key = bool(settings.get("gemini_api_key"))
    
    return {
        "gemini_api_key": "", # Mask key for security
        "database_type": settings.get("database_type", "sqlite"),
        "has_key": has_key
    }

@router.post("")
def update_system_settings(
    payload: Dict[str, str],
    current_user: User = Depends(get_current_admin)
):
    settings = load_local_settings()
    
    gemini_key = payload.get("gemini_api_key", "").strip()
    db_type = payload.get("database_type", "").strip()

    if gemini_key:
        settings["gemini_api_key"] = gemini_key
    if db_type:
        if db_type not in ["sqlite", "postgresql"]:
            raise HTTPException(status_code=400, detail="Unsupported database engine type.")
        settings["database_type"] = db_type

    save_local_settings(settings)
    return {"success": True, "message": "Global system configurations saved successfully."}

@router.post("/test-db")
def test_database_connection(
    payload: Dict[str, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Tests DB transaction flow."""
    try:
        db.execute(text("SELECT 1"))
        return {"success": True, "message": "Database connection verified."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
from sqlalchemy import text
