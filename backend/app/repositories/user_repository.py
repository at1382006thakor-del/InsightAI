from typing import Optional, List
from sqlalchemy.orm import Session
from .base_repository import BaseRepository
from ..database.models import User

class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def list_users(self) -> List[User]:
        return self.db.query(User).order_by(User.id.asc()).all()
