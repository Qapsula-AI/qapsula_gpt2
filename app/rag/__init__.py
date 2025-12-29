"""RAG модуль - Retrieval-Augmented Generation"""

try:
    from .rag_pipeline import RAGPipeline
    from .rag_retriever import Retriever
    from .rag_generator import Generator
    from .rag_ingest import DocumentIngestor
except ImportError as e:
    print(f"⚠️  Ошибка импорта RAG модулей: {e}")

__all__ = [
    'RAGPipeline',
    'Retriever',
    'Generator', 
    'DocumentIngestor',
]