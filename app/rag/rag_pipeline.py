from typing import List, Dict, Optional
from .retriever import Retriever
from .generator import Generator
from ..schemas import RAGResponse


class RAGPipeline:
    """Pipeline для RAG (Retrieval-Augmented Generation)"""
    
    def __init__(
        self,
        retriever: Retriever,
        generator: Generator,
        use_rag_threshold: float = 0.5
    ):
        self.retriever = retriever
        self.generator = generator
        self.use_rag_threshold = use_rag_threshold
    
    async def query(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        use_rag: bool = True,
        top_k: int = 3
    ) -> RAGResponse:
        """
        Обработать запрос через RAG pipeline
        
        Args:
            question: Вопрос пользователя
            chat_history: История чата
            use_rag: Использовать ли RAG
            top_k: Количество документов для retrieval
        
        Returns:
            RAGResponse с ответом и источниками
        """
        
        if not use_rag:
            # Генерируем ответ без RAG
            answer = await self.generator.generate_without_context(
                query=question,
                chat_history=chat_history
            )
            return RAGResponse(
                answer=answer,
                sources=[],
                confidence=0.0
            )
        
        # Retrieval: получаем релевантные документы
        documents = await self.retriever.retrieve_with_threshold(
            query=question,
            threshold=self.use_rag_threshold,
            k=top_k
        )
        
        if not documents:
            # Если релевантных документов нет, отвечаем без RAG
            answer = await self.generator.generate_without_context(
                query=question,
                chat_history=chat_history
            )
            return RAGResponse(
                answer=answer,
                sources=[],
                confidence=0.0
            )
        
        # Generation: генерируем ответ на основе документов
        answer = await self.generator.generate(
            query=question,
            documents=documents,
            chat_history=chat_history
        )
        
        # Собираем источники
        sources = []
        total_confidence = 0.0
        
        for doc, score in documents:
            source = doc.metadata.get('source', 'Unknown')
            if source not in sources:
                sources.append(source)
            total_confidence += score
        
        avg_confidence = total_confidence / len(documents) if documents else 0.0
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence=avg_confidence
        )
    
    async def ask(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Упрощенный метод для получения ответа
        
        Args:
            question: Вопрос
            chat_history: История чата
        
        Returns:
            Текст ответа
        """
        response = await self.query(question, chat_history)
        return response.answer
