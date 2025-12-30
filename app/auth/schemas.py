"""
Pydantic схемы для авторизации
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Запрос на авторизацию"""
    username: str = Field(..., min_length=3, max_length=100, description="Имя пользователя")
    password: str = Field(..., min_length=6, description="Пароль")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "secure_password"
            }
        }


class TokenResponse(BaseModel):
    """Ответ с JWT токеном"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Тип токена")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class UserResponse(BaseModel):
    """Данные пользователя для ответа API"""
    id: int = Field(..., description="ID пользователя")
    username: str = Field(..., description="Имя пользователя")
    email: str = Field(..., description="Email пользователя")
    full_name: Optional[str] = Field(None, description="Полное имя")
    is_active: bool = Field(default=True, description="Активен ли пользователь")
    is_superuser: bool = Field(default=False, description="Является ли суперпользователем")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    last_login_at: Optional[datetime] = Field(None, description="Последний вход")

    class Config:
        from_attributes = True  # Для работы с SQLAlchemy моделями
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "admin",
                "email": "admin@qapsula.local",
                "full_name": "Administrator",
                "is_active": True,
                "is_superuser": True,
                "created_at": "2025-12-30T10:00:00",
                "last_login_at": "2025-12-30T15:30:00"
            }
        }