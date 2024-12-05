import re
from datetime import datetime

import bcrypt
from sqlalchemy import Column, Integer, String, DateTime
from member.authentication import hash_password
from config.database import Base

class Member(Base):
    __tablename__ = "service_member"
    id = Column(Integer, primary_key=True)
    username = Column(String(16), unique=True)
    password = Column(String(60))   # bcrypt 60자
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

    def update_password(self, password: str):
        if self._is_bcrypt_pattern(password):
            raise ValueError("Password must be plain text")

        hashed_password = hash_password(password)
        self.password = hashed_password