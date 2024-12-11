from fastapi import Depends
from sqlalchemy.orm import Session

from config.database.connection import get_session
from feed.models import Post, PostComment


class PostRepository:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, post: Post):
        self.session.add(post)
        self.session.commit()

    def get_posts(self):
        return self.session.query(Post).order_by(Post.created_at.desc()).all()

    def get_post(self, post_id: int) -> Post | None:
        return self.session.query(Post).filter_by(id=post_id).first()


    def delete(self, post: Post):
        self.session.delete(post)
        self.session.commit()

    def delete_my_post(self, user_id: int, post_id: int) -> None:
        # 두 조건을 모두 만족하는 게시글이 있으면 삭제
        # 없으면 아무 동작도 하지 않음
        self.session.query(Post).filter_by(user_id=user_id, id=post_id).delete()
        self.session.commit()


class PostCommentRepository:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, comment: PostComment):
        self.session.add(comment)
        self.session.commit()

    def get_comment(self, comment_id: int) -> PostComment | None:
        return self.session.query(PostComment).filter_by(id=comment_id).first()