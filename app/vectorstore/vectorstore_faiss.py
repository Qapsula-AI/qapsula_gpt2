from typing import List, Tuple
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os
from .vectorstore_base import BaseVectorStore
from ..schemas import Document


class FAISSVectorStore(BaseVectorStore):
    """FAISS векторное хранилище с sentence-transformers"""
    
    def __init__(self, embedding_model: str = "paraphrase-multilingual-mpnet-base-v2"):
        self.encoder = SentenceTransformer(embedding_model)
        self.dimension = self.encoder.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents: List[Document] = []
    
    async def add_documents(self, documents: List[Document]):
        """Добавить документы в хранилище"""
        if not documents:
            return
        
        # Генерируем эмбеддинги
        texts = [doc.content for doc in documents]
        embeddings = self.encoder.encode(texts, convert_to_numpy=True)
        
        # Добавляем в FAISS индекс
        self.index.add(embeddings.astype('float32'))
        
        # Сохраняем документы
        for i, doc in enumerate(documents):
            doc.embedding = embeddings[i].tolist()
            self.documents.append(doc)
    
    async def similarity_search(
        self,
        query: str,
        k: int = 3
    ) -> List[Tuple[Document, float]]:
        """Поиск похожих документов"""
        if self.index.ntotal == 0:
            return []
        
        # Генерируем эмбеддинг запроса
        query_embedding = self.encoder.encode([query], convert_to_numpy=True)
        
        # Ищем похожие векторы
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
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
