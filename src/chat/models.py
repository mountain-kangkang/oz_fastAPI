from datetime import datetime

from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, String

from config.database.orm import Base


class ChatRoom(Base):
    __tablename__ = 'chat_room'

    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)


class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('service_member.id'))
    chat_room_id = Column(Integer, ForeignKey('chat_room.id'), nullable=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    @classmethod
    def create(cls, room_id: int, user_id: int, content: str):
        return cls(chat_room_id=room_id, user_id=user_id, content=content)