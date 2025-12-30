"""
SQLAlchemy модели для базы данных.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.db.database import Base


class User(Base):
    """Пользователи системы для авторизации."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Авторизация
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Информация о пользователе
    full_name = Column(String(255), nullable=True)

    # Статус
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"