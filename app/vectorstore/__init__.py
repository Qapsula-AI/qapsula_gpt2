"""Модуль векторного хранилища"""

try:
    from .vectorstore_base import BaseVectorStore
    from .vectorstore_faiss import FAISSVectorStore
except ImportError as e:
    print(f"⚠️  Ошибка импорта vectorstore модулей: {e}")

__all__ = ['BaseVectorStore', 'FAISSVectorStore']