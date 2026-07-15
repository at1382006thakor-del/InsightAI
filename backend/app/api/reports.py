from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Any
import os
import uuid

from ..database.connection import get_db
from ..database.models import Report, User, Notification
from ..schemas.reports import ReportListItem, ReportGenerateRequest
from ..services.auth_service import get_current_user
from ..services.ai_service import generate_ai_business_report
from ..reports.pdf_generator import build_pdf_report
from ..reports.pptx_generator import build_pptx_report

router = APIRouter(prefix="/reports", tags=["Business Reports"])

@router.get("/list", response_model=List[ReportListItem])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Lists all previously compiled BI and sales strategy reports."""
    reports = db.query(Report).filter(Report.user_id == current_user.id).order_by(Report.generated_at.desc()).all()
    # Map old columns to new columns dynamically if needed (backward compatibility check)
    result = []
    for r in reports:
        result.append(ReportListItem(
            report_id=str(r.report_id),
            type=r.type,
            file_format=r.file_format or "pdf",
            generated_at=r.generated_at,
            file_path=r.file_path or r.pdf_path, # fallback
            summary_text=r.summary_text
        ))
    return result

@router.post("/generate", response_model=ReportListItem, status_code=status.HTTP_201_CREATED)
def generate_report(
    payload: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Generates an AI strategy report, compiles PDF or PowerPoint slide presentation, and stores metadata logs."""
    # 1. Verify access role: only Admins and Analysts can trigger report compilation
    if current_user.role not in ["admin", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and sales analysts can compile performance strategy reports."
        )

    # 2. Draft strategic highlights in Markdown (Gemini / fallback)
    summary_text = generate_ai_business_report(db, payload.report_type)
    
    # 3. Generate documents based on requested format
    report_id = str(uuid.uuid4())
    try:
        if payload.file_format == "pptx":
            file_path = build_pptx_report(db, payload.report_type, summary_text)
        else:
            file_path = build_pdf_report(db, payload.report_type, summary_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategy report compile failed: {str(e)}"
        )

    # 4. Save metadata records in DB
    db_report = Report(
        report_id=report_id,
        user_id=current_user.id,
        type=payload.report_type,
        file_format=payload.file_format or "pdf",
        file_path=file_path,
        summary_text=summary_text
    )
    db.add(db_report)
    
    # Generate system notification log
    alert = Notification(
        title="Business Report Compiled",
        message=f"A new {payload.report_type.capitalize()} strategy {payload.file_format.upper()} report is ready for download.",
        type="success"
    )
    db.add(alert)
    db.commit()
    db.refresh(db_report)

    return ReportListItem(
        report_id=db_report.report_id,
        type=db_report.type,
        file_format=db_report.file_format,
        generated_at=db_report.generated_at,
        file_path=db_report.file_path,
        summary_text=db_report.summary_text
    )

@router.get("/download/{report_id}")
def download_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Downloads a specific PDF/PPTX report file."""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report metadata record not found in system.")
        
    file_path = report.file_path or getattr(report, 'pdf_path', None)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report document file does not exist on disk storage.")

    filename = os.path.basename(file_path)
    media_type = "application/pdf" if report.file_format == "pdf" else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    
    return FileResponse(
        file_path, 
        media_type=media_type, 
        filename=filename
    )
