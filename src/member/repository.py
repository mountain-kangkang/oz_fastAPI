from fastapi import Depends
from sqlalchemy.orm import Session

from config.database.connection import get_session
from member.models import Member, SocialProvider


# DB에 작업(생성, 조회, 수정, 삭제)
class MemberRepository:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, member: Member) -> None:
        self.session.add(member)
        self.session.commit()

    def get_member_by_username(self, username: str) -> Member | None:
        return self.session.query(Member).filter(Member.username == username).first()

    def get_member_by_id(self, user_id: int) -> Member | None:
        return self.session.query(Member).filter(Member.id == user_id).first()

    def get_member_by_social_email(self, social_provider: SocialProvider, email: str) -> Member | None:
        return self.session.query(Member).filter(
            Member.social_provider == social_provider,
            Member.email == email
        ).first()

    def delete(self, member: Member) -> None:
        self.session.delete(member)
        self.session.commit()