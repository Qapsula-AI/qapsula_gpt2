"""
FastAPI dependencies для защиты endpoints
"""

from datetime import datetime
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from .jwt_handler import verify_token

# OAuth2 схема для Bearer токенов
# tokenUrl указывает на endpoint для получения токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency для получения текущего пользователя из JWT токена

    Args:
        token: JWT токен из заголовка Authorization
        db: Сессия базы данных

    Returns:
        User: Объект пользователя из БД

    Raises:
        HTTPException: 401 если токен невалиден или пользователь не найден

    Example:
        ```python
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"username": current_user.username}
        ```
    """
    # Проверяем и декодируем токен
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен или срок действия истек",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Получаем username из токена
    username: Optional[str] = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не содержит информацию о пользователе",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ищем пользователя в БД
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем активен ли пользователь
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован",
        )

    # Обновляем время последнего входа
    user.last_login_at = datetime.utcnow()
    db.commit()

    return user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency для проверки прав администратора

    Args:
        current_user: Текущий пользователь (из get_current_user)

    Returns:
        User: Объект пользователя с правами админа

    Raises:
        HTTPException: 403 если пользователь не является администратором

    Example:
        ```python
        @app.delete("/users/{user_id}")
        async def delete_user(
            user_id: int,
            admin: User = Depends(require_admin)
        ):
            # Только админы могут удалять пользователей
            ...
        ```
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора",
        )

    return current_user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency для получения активного пользователя
    (дополнительная проверка активности - уже есть в get_current_user)

    Args:
        current_user: Текущий пользователь

    Returns:
        User: Активный пользователь

    Note:
        Эта функция оставлена для совместимости, но проверка активности
        уже выполняется в get_current_user
    """
    return current_user