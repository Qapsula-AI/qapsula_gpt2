from typing import List, Tuple
from ..vectorstore.vectorstore_base import BaseVectorStore
from ..schemas import Document


class Retriever:
    """Retriever для поиска релевантных документов"""
    
    def __init__(self, vectorstore: BaseVectorStore, top_k: int = 3):
        self.vectorstore = vectorstore
        self.top_k = top_k
    
    async def retrieve(self, query: str, k: int = None) -> List[Tuple[Document, float]]:
        """
        Получить релевантные документы
        
        Args:
            query: Поисковый запрос
            k: Количество документов (если None, используется self.top_k)
        
        Returns:
            Список кортежей (документ, score)
        """
        k = k or self.top_k
        results = await self.vectorstore.similarity_search(query, k=k)
        return results
    
    async def retrieve_with_threshold(
        self, 
        query: str, 
        threshold: float = 0.5,
        k: int = None
    ) -> List[Tuple[Document, float]]:
        """
        Получить документы с порогом релевантности
        
        Args:
            query: Поисковый запрос
            threshold: Минимальный порог similarity (0-1)
            k: Количество документов
        
        Returns:
            Отфильтрованный список документов
        """
        results = await self.retrieve(query, k)
        return [(doc, score) for doc, score in results if score >= threshold]
