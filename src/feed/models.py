from datetime import datetime

from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship, backref

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

    @property   # 커스텀하게 정의하는 속성
    def image_static_path(self) -> str:
        filename: str = self.image.split("/")[-1]
        return f"http://127.0.0.1:8000/static/{filename}"


    @classmethod
    def create(cls, user_id: int, image: str, content: str):
        return cls(user_id=user_id, image=image, content=content)

    def update_content(self, content: str):
        # 욕설 필터링
        if "f-word" in content:
            raise ValueError("Content should not be f-word")
        self.content = content


class PostComment(Base):
    __tablename__ = 'post_comment'
    id = Column(Integer, primary_key=True)
    # 댓글 작성자
    user_id = Column(Integer, ForeignKey('service_member.id'), nullable=False)
    # 게시글
    post_id = Column(Integer, ForeignKey('feed_post.id'), nullable=False)
    content = Column(Text, nullable=False)  # 댓글 내용

    # 댓글 & 대댓글 관계 표현
    parent_id = Column(Integer, ForeignKey('post_comment.id'), nullable=True)

    created_at = Column(DateTime, default=datetime.now, nullable=False)

    post = relationship(Post, backref='comments')
    parent = relationship(
        "PostComment",
        remote_side=[id],
        # 자식 댓글은 삭제되지 않음(자식 댓글이 부모 댓글로 승격)
        # backref="replies"

        # 부모 객체 삭제시, 자식 객체가 함께 삭제(delete-orphan)
        backref=backref("replies", cascade="all, delete-orphan")
    )

    @property
    def is_parent(self) -> bool:
        return self.parent_id is None

    @classmethod
    def create(cls, user_id: int, post_id: int, content: str, parent_id: int | None):
        return cls(user_id=user_id, post_id=post_id, content=content, parent_id=parent_id)


class PostLike(Base):
    __tablename__ = 'post_like'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('service_member.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('feed_post.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', name='uq_post_like_user_post'),
    )

    @classmethod
    def create(cls, user_id: int, post_id: int):
        return cls(user_id=user_id, post_id=post_id)

    # 사용자가 Like 버튼 -> PostLike(user_id, post_id) 기록
    # 중복 생성 방지
    # 사용자가 Like 버튼 취소 -> PostLike(user_id, post_id) 삭제

    # 사용자가 싫어요