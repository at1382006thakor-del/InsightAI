from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
import os
import shutil
import uuid

from ..database.connection import get_db
from ..database.models import User, Dataset, Notification
from ..repositories.dataset_repository import DatasetRepository
from ..repositories.sale_repository import SaleRepository
from ..services.auth_service import get_current_admin
from ..services.cleaning import analyze_dataset

router = APIRouter(prefix="/datasets", tags=["Dataset Management"])

UPLOAD_DIR = "datasets"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("")
def list_uploaded_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    repo = DatasetRepository(db)
    return repo.list_datasets()

@router.post("/upload")
async def upload_raw_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin)
):
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".csv", ".xls", ".xlsx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only CSV, XLS, or XLSX are supported."
        )

    # Save to temp location
    temp_id = str(uuid.uuid4())
    temp_filename = f"temp_{temp_id}_{file.filename}"
    temp_path = os.path.join(UPLOAD_DIR, temp_filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write file to storage: {str(e)}"
        )

    # Analyze file structural qualities
    try:
        analysis = analyze_dataset(temp_path)
        return analysis
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis of dataset failed: {str(e)}"
        )

@router.patch("/{id}/active")
def toggle_active_dataset(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    repo = DatasetRepository(db)
    dataset = repo.get_by_id(id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset record not found.")

    # Deactivate all others first
    repo.deactivate_all()
    
    # Toggle target active
    dataset.is_active = True
    repo.update()

    # Generate system notification
    alert = Notification(
        title="Active Dataset Switched",
        message=f"Dataset '{dataset.filename}' is now set as the active data source.",
        type="info"
    )
    db.add(alert)
    db.commit()

    return {"success": True, "message": f"Dataset '{dataset.filename}' set as active."}

@router.delete("/{id}")
def delete_dataset(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    dataset_repo = DatasetRepository(db)
    sale_repo = SaleRepository(db)
    
    dataset = dataset_repo.get_by_id(id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset record not found.")

    # 1. Cascade wipe sales, products, and customers associated
    sale_repo.delete_by_dataset(id)

    # 2. Delete file on disk if exists
    if os.path.exists(dataset.file_path):
        try:
            os.remove(dataset.file_path)
        except Exception:
            pass

    # 3. Delete metadata record
    dataset_repo.delete(dataset)

    # Generate system alert notification
    alert = Notification(
        title="Dataset Deleted",
        message=f"Spreadsheet '{dataset.filename}' and all associated transactions permanently deleted.",
        type="warning"
    )
    db.add(alert)
    db.commit()

    return {"success": True, "message": f"Dataset '{dataset.filename}' and records wiped."}
