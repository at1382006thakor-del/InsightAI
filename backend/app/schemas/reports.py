from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReportListItem(BaseModel):
    report_id: str
    type: str
    file_format: str
    generated_at: datetime
    file_path: str
    summary_text: Optional[str] = None

    class Config:
        from_attributes = True

class ReportGenerateRequest(BaseModel):
    report_type: str  # "daily", "weekly", "monthly", "quarterly", "annual"
    file_format: Optional[str] = "pdf"  # "pdf" or "pptx"
