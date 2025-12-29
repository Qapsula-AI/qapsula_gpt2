"""Ядро приложения - менеджеры и основные компоненты"""

try:
    from .rag_manager import RAGManager
except ImportError as e:
    print(f"⚠️  Ошибка импорта core модулей: {e}")

__all__ = ['RAGManager']