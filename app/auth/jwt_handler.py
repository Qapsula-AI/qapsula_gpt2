"""
JWT токены - создание и валидация
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError

# Конфигурация JWT
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY не установлен в переменных окружения. "
        "Сгенерируйте его с помощью: openssl rand -hex 32"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создать JWT access token

    Args:
        data: Данные для включения в токен (обычно {"sub": username, "user_id": id})
        expires_delta: Опциональное время жизни токена (по умолчанию из настроек)

    Returns:
        str: Закодированный JWT токен

    Example:
        >>> token = create_access_token({"sub": "admin", "user_id": 1})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()

    # Устанавливаем время истечения токена
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # Кодируем токен
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Проверить и декодировать JWT токен

    Args:
        token: JWT токен для проверки

    Returns:
        Optional[Dict[str, Any]]: Декодированные данные токена или None если токен невалиден

    Example:
        >>> token = create_access_token({"sub": "admin", "user_id": 1})
        >>> payload = verify_token(token)
        >>> print(payload)
        {'sub': 'admin', 'user_id': 1, 'exp': ...}
    """
    try:
        # Декодируем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # Токен невалиден или истек
        return None


def get_token_subject(token: str) -> Optional[str]:
    """
    Получить subject (username) из токена

    Args:
        token: JWT токен

    Returns:
        Optional[str]: Username из токена или None

    Example:
        >>> token = create_access_token({"sub": "admin"})
        >>> username = get_token_subject(token)
        >>> print(username)
        admin
    """
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None