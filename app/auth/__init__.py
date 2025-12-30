"""
Модуль авторизации и аутентификации
Включает JWT токены, хеширование паролей и FastAPI dependencies
"""

from .password import hash_password, verify_password
from .jwt_handler import create_access_token, verify_token
from .dependencies import get_current_user, require_admin
from .schemas import LoginRequest, TokenResponse, UserResponse

__all__ = [
    'hash_password',
    'verify_password',
    'create_access_token',
    'verify_token',
    'get_current_user',
    'require_admin',
    'LoginRequest',
    'TokenResponse',
    'UserResponse',
]