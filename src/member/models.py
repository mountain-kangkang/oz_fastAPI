from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from config.database import Base

class Member(Base):
    __tablename__ = "service_member"
    id = Column(Integer, primary_key=True)
    username = Column(String(16), unique=True)
    password = Column(String(60))
    created_at = Column(DateTime, default=datetime.now)

