from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..database.connection import get_db
from ..database.models import User
from ..repositories.user_repository import UserRepository
from ..services.auth_service import get_current_admin

router = APIRouter(prefix="/users", tags=["User Management"])

@router.get("")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    repo = UserRepository(db)
    users = repo.list_users()
    
    # Return formatted list (excluding password hashes)
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "created_at": u.created_at
        } for u in users
    ]

@router.patch("/{id}/role")
def update_user_role(
    id: int,
    payload: Dict[str, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    repo = UserRepository(db)
    user = repo.get_by_id(id)
    if not user:
        raise HTTPException(status_code=404, detail="User record not found.")

    new_role = payload.get("role")
    if new_role not in ["admin", "analyst", "viewer"]:
        raise HTTPException(status_code=400, detail="Invalid role specified.")

    # Prevent admin self-role change to maintain at least one admin
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot change your own administrative role.")

    user.role = new_role
    repo.update()

    return {"success": True, "message": f"User role modified to '{new_role}'."}

@router.delete("/{id}")
def delete_user_account(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    repo = UserRepository(db)
    user = repo.get_by_id(id)
    if not user:
        raise HTTPException(status_code=404, detail="User record not found.")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own active admin account.")

    repo.delete(user)
    return {"success": True, "message": "User account permanently deleted."}
over_write = True
