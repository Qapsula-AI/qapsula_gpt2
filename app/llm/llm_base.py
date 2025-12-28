from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseLLM(ABC):
    """Базовый класс для LLM"""
    
    def __init__(self, model_name: str, temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
    
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        context: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 1000
    ) -> str:
        """
        Генерация ответа
        
        Args:
            prompt: Текст запроса
            context: История сообщений
            max_tokens: Максимальное количество токенов
        
        Returns:
            Сгенерированный текст
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 1000
    ):
        """Генерация ответа с потоковой передачей"""
        pass
