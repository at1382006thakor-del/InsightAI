from typing import List, Optional
from sqlalchemy.orm import Session
from .base_repository import BaseRepository
from ..database.models import Report

class ReportRepository(BaseRepository[Report]):
    def __init__(self, db: Session):
        super().__init__(Report, db)

    def list_reports(self, user_id: int) -> List[Report]:
        return self.db.query(Report).filter(Report.user_id == user_id).order_by(Report.generated_at.desc()).all()

    def get_report_by_id(self, report_id: str) -> Optional[Report]:
        return self.db.query(Report).filter(Report.report_id == report_id).first()
