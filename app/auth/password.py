"""
Утилиты для работы с паролями
Использует bcrypt для безопасного хеширования
"""

from passlib.context import CryptContext

# Настройка контекста для bcrypt (12 rounds - баланс между безопасностью и производительностью)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Хеширует пароль используя bcrypt

    Args:
        password: Пароль в открытом виде

    Returns:
        str: Хешированный пароль

    Example:
        >>> hashed = hash_password("my_secret_password")
        >>> print(hashed)
        $2b$12$...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля хешу

    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хешированный пароль из БД

    Returns:
        bool: True если пароль совпадает, False иначе

    Example:
        >>> hashed = hash_password("my_password")
        >>> verify_password("my_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)