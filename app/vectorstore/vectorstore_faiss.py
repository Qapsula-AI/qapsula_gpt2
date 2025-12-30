from typing import List, Tuple
import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings
import pickle
import os
from .vectorstore_base import BaseVectorStore
from ..schemas import Document


class FAISSVectorStore(BaseVectorStore):
    """FAISS векторное хранилище с OpenAI Embeddings"""

    def __init__(self, embedding_model: str = "text-embedding-3-small"):
        """
        Args:
            embedding_model: OpenAI модель эмбеддингов
                - text-embedding-3-small (1536 dims, $0.02/1M tokens) - рекомендуется
                - text-embedding-3-large (3072 dims, $0.13/1M tokens)
                - text-embedding-ada-002 (1536 dims, $0.10/1M tokens) - legacy
        """
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        # Размерность для text-embedding-3-small и ada-002
        self.dimension = 1536 if "small" in embedding_model or "ada" in embedding_model else 3072
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents: List[Document] = []
    
    async def add_documents(self, documents: List[Document]):
        """Добавить документы в хранилище"""
        if not documents:
            return

        # Генерируем эмбеддинги через OpenAI API
        texts = [doc.content for doc in documents]
        embeddings_list = await self.embeddings.aembed_documents(texts)
        embeddings_array = np.array(embeddings_list, dtype='float32')

        # Добавляем в FAISS индекс
        self.index.add(embeddings_array)

        # Сохраняем документы
        for i, doc in enumerate(documents):
            doc.embedding = embeddings_list[i]
            self.documents.append(doc)
    
    async def similarity_search(
        self,
        query: str,
        k: int = 3
    ) -> List[Tuple[Document, float]]:
        """Поиск похожих документов"""
        if self.index.ntotal == 0:
            return []

        # Генерируем эмбеддинг запроса через OpenAI API
        query_embedding_list = await self.embeddings.aembed_query(query)
        query_embedding = np.array([query_embedding_list], dtype='float32')

        # Ищем похожие векторы
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, k)

        # Формируем результаты
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx]
                similarity = 1 / (1 + distances[0][i])  # Конвертируем расстояние в similarity
                results.append((doc, similarity))

        return results
    
    async def save(self, path: str):
        """Сохранить хранилище на диск"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Сохраняем FAISS индекс
        faiss.write_index(self.index, f"{path}.index")
        
        # Сохраняем документы
        with open(f"{path}.docs", 'wb') as f:
            pickle.dump(self.documents, f)
    
    async def load(self, path: str):
        """Загрузить хранилище с диска"""
        if os.path.exists(f"{path}.index"):
            self.index = faiss.read_index(f"{path}.index")
        
        if os.path.exists(f"{path}.docs"):
            with open(f"{path}.docs", 'rb') as f:
                self.documents = pickle.load(f)
