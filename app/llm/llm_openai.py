from typing import List, Dict, Optional
from openai import AsyncOpenAI
from .llm_base import BaseLLM
import os


class OpenAILLM(BaseLLM):
    """OpenAI GPT реализация"""
    
    def __init__(
        self, 
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        api_key: Optional[str] = None
    ):
        super().__init__(model_name, temperature)
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    async def generate(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 1000
    ) -> str:
        """Генерация ответа через OpenAI API"""
        messages = []
        
        # Системное сообщение
        messages.append({
            "role": "system",
            "content": "Ты полезный AI ассистент. Отвечай на русском языке кратко и по существу."
        })
        
        # Добавляем контекст
        if context:
            messages.extend(context)
        
        # Добавляем текущий промпт
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при генерации ответа: {str(e)}"
    
    async def generate_stream(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 1000
    ):
        """Генерация ответа с потоковой передачей"""
        messages = []
        
        messages.append({
            "role": "system",
            "content": "Ты полезный AI ассистент. Отвечай на русском языке кратко и по существу."
        })
        
        if context:
            messages.extend(context)
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Ошибка: {str(e)}"
