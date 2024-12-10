from datetime import datetime

from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from config.database.orm import Base
from member.models import Member


class Post(Base):
    __tablename__ = 'feed_post'

    # 실제 DB 컬럼
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('service_member.id'), nullable=False)
    image = Column(String(256), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # ORM 관계 정의
    user = relationship(Member, backref='posts')

    @classmethod
    def create(cls, user_id: int, image: str, content: str):
        return cls(user_id=user_id, image=image, content=content)