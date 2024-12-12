from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chat.models import ChatMessage
from config.database.connection_async import get_async_session


class ChatRepository:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def save(self, message: ChatMessage) -> None:
        self.session.add(message)
        await self.session.commit()

    async def get_messages_by_room(self, room_id: int):
        # DB에서 조회
        result = await self.session.execute(
            select(ChatMessage).filter_by(chat_room_id=room_id).order_by(ChatMessage.created_at.asc())
        )

        # 데이터를 ORM 객체로 변환(I/O 대기 없음)
        return result.scalars().all()
        # return self.session.query(ChatMessage).order_by(ChatMessage.created_at.desc()).all()

