import os
from typing import List
from pathlib import Path
from ..schemas import Document
from ..vectorstore.vectorstore_base import BaseVectorStore


class DocumentIngestor:
    """Класс для загрузки и обработки документов"""
    
    def __init__(self, vectorstore: BaseVectorStore):
        self.vectorstore = vectorstore
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Разбить текст на чанки
        
        Args:
            text: Исходный текст
            chunk_size: Размер чанка в символах
            overlap: Перекрытие между чанками
        
        Returns:
            Список текстовых чанков
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Пытаемся разбить по предложениям
            if end < text_len:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                split_point = max(last_period, last_newline)
                
                if split_point > chunk_size // 2:
                    chunk = chunk[:split_point + 1]
                    end = start + split_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    async def ingest_text(self, text: str, metadata: dict = None) -> int:
        """
        Загрузить текст в векторное хранилище
        
        Args:
            text: Текст для загрузки
            metadata: Метаданные документа
        
        Returns:
            Количество созданных чанков
        """
        chunks = self._chunk_text(text)
        documents = []
        
        for i, chunk in enumerate(chunks):
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata['chunk_id'] = i
            doc_metadata['total_chunks'] = len(chunks)
            
            documents.append(Document(
                content=chunk,
                metadata=doc_metadata
            ))
        
        await self.vectorstore.add_documents(documents)
        return len(documents)
    
    async def ingest_file(self, file_path: str) -> int:
        """
        Загрузить файл в векторное хранилище
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            Количество созданных чанков
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        metadata = {
            'source': str(path.name),
            'file_path': str(path)
        }
        
        return await self.ingest_text(text, metadata)
    
    async def ingest_directory(self, directory_path: str, extensions: List[str] = None) -> int:
        """
        Загрузить все файлы из директории
        
        Args:
            directory_path: Путь к директории
            extensions: Список расширений файлов (например, ['.txt', '.md'])
        
        Returns:
            Общее количество созданных чанков
        """
        if extensions is None:
            extensions = ['.txt', '.md']
        
        path = Path(directory_path)
        total_chunks = 0
        
        for file_path in path.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                try:
                    chunks = await self.ingest_file(str(file_path))
                    total_chunks += chunks
                    print(f"✓ Загружен: {file_path.name} ({chunks} чанков)")
                except Exception as e:
                    print(f"✗ Ошибка при загрузке {file_path.name}: {e}")
        
        return total_chunks
