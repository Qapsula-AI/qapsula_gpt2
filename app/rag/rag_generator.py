from typing import List, Dict, Tuple
from ..llm.llm_base import BaseLLM
from ..schemas import Document


class Generator:
    """Generator для создания ответов на основе контекста"""
    
    def __init__(self, llm: BaseLLM):
        self.llm = llm
    
    def _create_rag_prompt(
        self,
        query: str,
        documents: List[Tuple[Document, float]]
    ) -> str:
        """Создать промпт для RAG с контекстом"""
        
        if not documents:
            return query
        
        context_parts = []
        for i, (doc, score) in enumerate(documents, 1):
            context_parts.append(f"[Источник {i}]\n{doc.content}\n")
        
        context = "\n".join(context_parts)
        
        prompt = f"""На основе следующего контекста ответь на вопрос пользователя.

Контекст:
{context}

Вопрос: {query}

Инструкции:
- Используй информацию из контекста для ответа
- Если в контексте нет информации для ответа, скажи об этом
- Отвечай на русском языке
- Будь кратким и точным

Ответ:"""
        
        return prompt
    
    async def generate(
        self,
        query: str,
        documents: List[Tuple[Document, float]],
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Сгенерировать ответ на основе документов
        
        Args:
            query: Запрос пользователя
            documents: Релевантные документы с scores
            chat_history: История чата
        
        Returns:
            Сгенерированный ответ
        """
        prompt = self._create_rag_prompt(query, documents)
        response = await self.llm.generate(
            prompt=prompt,
            context=chat_history,
            max_tokens=1000
        )
        return response
    
    async def generate_without_context(
        self,
        query: str,
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """Сгенерировать ответ без RAG контекста"""
        print(f"🤖 Generator: начало генерации ответа без контекста...")
        print(f"📝 Generator: запрос: {query[:50]}...")
        response = await self.llm.generate(
            prompt=query,
            context=chat_history,
            max_tokens=100  # Уменьшено для быстрой генерации
        )
        print(f"✅ Generator: ответ получен ({len(response)} символов)")
        return response
