from abc import ABC, abstractmethod
from typing import List, Tuple
from ..schemas import Document


class BaseVectorStore(ABC):
    """Базовый класс для векторного хранилища"""
    
    @abstractmethod
    async def add_documents(self, documents: List[Document]):
        """Добавить документы в хранилище"""
        pass
    
    @abstractmethod
    async def similarity_search(
        self, 
        query: str, 
        k: int = 3
    ) -> List[Tuple[Document, float]]:
        """
        Поиск похожих документов
        
        Args:
            query: Поисковый запрос
            k: Количество результатов
        
        Returns:
            Список кортежей (документ, similarity_score)
        """
        pass
    
    @abstractmethod
    async def save(self, path: str):
        """Сохранить хранилище на диск"""
        pass
    
    @abstractmethod
    async def load(self, path: str):
        """Загрузить хранилище с диска"""
        pass
