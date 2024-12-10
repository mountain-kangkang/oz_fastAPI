from fastapi import Depends
from sqlalchemy.orm import Session

from config.database.connection import get_session
from feed.models import Post


class PostRepository:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, post: Post):
        self.session.add(post)
        self.session.commit()

    def get_posts(self):
        return self.session.query(Post).order_by(Post.created_at.desc()).all()