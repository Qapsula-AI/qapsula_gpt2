"""API модуль для Telegram бота и FastAPI"""

try:
    from .fastapi_app import app as fastapi_app
    from .telegram_bot import TelegramBot
except ImportError as e:
    print(f"⚠️  Ошибка импорта API модулей: {e}")

__all__ = ['fastapi_app', 'TelegramBot']