import random
import re
import string
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Column, Integer, String, DateTime
from member.service.authentication import hash_password
from config.database.orm import Base


class SocialProvider(StrEnum):
    KAKAO = "kakao"
    NAVER = "naver"
    GOOGLE = "google"

class Member(Base):
    __tablename__ = "service_member"
    id = Column(Integer, primary_key=True)
    username = Column(String(16), unique=True, nullable=False)
    email = Column(String(256), nullable=True)
    social_provider = Column(String(8), nullable=True)
    password = Column(String(60), nullable=False)   # bcrypt 60자
    created_at = Column(DateTime, default=datetime.now)

    @staticmethod
    def _is_bcrypt_pattern(password: str):
        bcrypt_pattern = r'^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$'
        return re.match(bcrypt_pattern, password) is not None

    @classmethod
    def create(cls, username: str, password:str):
        if cls._is_bcrypt_pattern(password):
            raise ValueError("Password must be plain text")

        hashed_password = hash_password(password)
        return cls(username=username, password=hashed_password)

    @classmethod
    def social_signup(cls, social_provider: SocialProvider, subject: str, email: str):
        # 소셜 회원가입
        # : 사용자가 username 입력 안함
        # : username 만들어줘야 됨
        username: str = f"#{social_provider[:2]}#{subject}"
        paasword: str = "".join(random.choices(string.ascii_letters, k=16))
        hashed_password = hash_password(plain_text=paasword)

        return cls(username=username, password=hashed_password, social_provider=social_provider, email=email)

    def update_password(self, password: str):
        if self._is_bcrypt_pattern(password):
            raise ValueError("Password must be plain text")

        hashed_password = hash_password(password)
        self.password = hashed_password

    def update_email(self, email: str):
        self.email = email