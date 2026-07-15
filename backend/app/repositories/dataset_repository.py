from typing import Optional, List
from sqlalchemy.orm import Session
from .base_repository import BaseRepository
from ..database.models import Dataset

class DatasetRepository(BaseRepository[Dataset]):
    def __init__(self, db: Session):
        super().__init__(Dataset, db)

    def list_datasets(self) -> List[Dataset]:
        return self.db.query(Dataset).order_by(Dataset.upload_date.desc()).all()

    def get_active_dataset(self) -> Optional[Dataset]:
        return self.db.query(Dataset).filter(Dataset.is_active == True).first()

    def deactivate_all(self) -> None:
        self.db.query(Dataset).update({Dataset.is_active: False})
        self.db.commit()
