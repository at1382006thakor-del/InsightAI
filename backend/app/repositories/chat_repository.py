from typing import List, Optional
from sqlalchemy.orm import Session
from ..database.models import Conversation, Message

class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_conversations(self, user_id: int) -> List[Conversation]:
        return self.db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).all()

    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def create_conversation(self, user_id: int, title: str) -> Conversation:
        conv = Conversation(user_id=user_id, title=title)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def delete_conversation(self, conversation_id: int) -> None:
        self.db.query(Conversation).filter(Conversation.id == conversation_id).delete()
        self.db.commit()

    def get_messages(self, conversation_id: int) -> List[Message]:
        return self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()

    def save_message(self, conversation_id: int, sender: str, message: str, chart_metadata: dict = None) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            sender=sender,
            message=message,
            chart_metadata=chart_metadata or {}
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg
