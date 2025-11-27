from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from ..db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    display_name = Column(String(128), nullable=True)
    role = Column(String(32), default="user", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
