# app/__init__.py
"""
Telegram RAG Bot - AI-powered bot with Retrieval-Augmented Generation
"""
__version__ = "1.0.0"

# app/api/__init__.py
"""
API модули для взаимодействия с внешними сервисами
"""
from .telegram import TelegramBot

__all__ = ['TelegramBot']

# app/llm/__init__.py
"""
LLM модули для работы с языковыми моделями
"""
from .base import BaseLLM
from .openai import OpenAILLM

__all__ = ['BaseLLM', 'OpenAILLM']

# app/vectorstore/__init__.py
"""
Векторные хранилища для семантического поиска
"""
from .base import BaseVectorStore
from .faiss import FAISSVectorStore

__all__ = ['BaseVectorStore', 'FAISSVectorStore']

# app/rag/__init__.py
"""
RAG (Retrieval-Augmented Generation) компоненты
"""
from .ingest import DocumentIngestor
from .retriever import Retriever
from .generator import Generator
from .pipeline import RAGPipeline

__all__ = [
    'DocumentIngestor',
    'Retriever', 
    'Generator',
    'RAGPipeline'
]
