from typing import List, Dict, Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from .llm_base import BaseLLM
import os


class OpenAILLM(BaseLLM):
    """OpenAI GPT реализация через LangChain провайдер"""

    def __init__(
        self,
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        api_key: Optional[str] = None,
        max_tokens: int = 1000
    ):
        super().__init__(model_name, temperature)
        self.max_tokens = max_tokens
        self.client = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            max_tokens=max_tokens
        )

    def _prepare_messages(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> List:
        """Подготовка сообщений для LangChain"""
        messages = []

        # Системное сообщение
        messages.append(SystemMessage(
            content="Ты полезный AI ассистент. Отвечай на русском языке кратко и по существу."
        ))

        # Добавляем контекст
        if context:
            for msg in context:
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))

        # Добавляем текущий промпт
        messages.append(HumanMessage(content=prompt))

        return messages

    async def generate(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Генерация ответа через OpenAI API (LangChain)"""
        try:
            messages = self._prepare_messages(prompt, context)

            # Используем переданный max_tokens или значение по умолчанию
            if max_tokens is not None:
                # Временно обновляем max_tokens для этого вызова
                original_max_tokens = self.client.max_tokens
                self.client.max_tokens = max_tokens
                response = await self.client.ainvoke(messages)
                self.client.max_tokens = original_max_tokens
            else:
                response = await self.client.ainvoke(messages)

            return response.content
        except Exception as e:
            return f"Ошибка при генерации ответа: {str(e)}"

    async def generate_stream(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Генерация ответа с потоковой передачей через LangChain"""
        try:
            messages = self._prepare_messages(prompt, context)

            # Используем переданный max_tokens или значение по умолчанию
            if max_tokens is not None:
                original_max_tokens = self.client.max_tokens
                self.client.max_tokens = max_tokens

                async for chunk in self.client.astream(messages):
                    if chunk.content:
                        yield chunk.content

                self.client.max_tokens = original_max_tokens
            else:
                async for chunk in self.client.astream(messages):
                    if chunk.content:
                        yield chunk.content
        except Exception as e:
            yield f"Ошибка: {str(e)}"
