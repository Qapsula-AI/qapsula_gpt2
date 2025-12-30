"""Qapsula GPT2 - Telegram бот с RAG архитектурой"""

__version__ = "1.0.0"
__author__ = "Qapsula AI"

# Экспорт основных компонентов
try:
    from .main_app import run as run_app
    from .core.rag_manager import RAGManager
    from .api.fastapi_app import app as fastapi_app
    from .api.telegram_bot import TelegramBot
except ImportError as e:
    print(f"⚠️  Ошибка импорта app модулей: {e}")

__all__ = [
    'run_app',
    'RAGManager',
    'fastapi_app', 
    'TelegramBot',
]