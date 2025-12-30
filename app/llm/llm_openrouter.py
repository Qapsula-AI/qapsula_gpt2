# Новый LLM-провайдер для OpenRouter (использует aiohttp, async)
import os
import json
from typing import List, Dict, Optional, AsyncGenerator
import aiohttp

from .llm_base import BaseLLM


class OpenRouterLLM(BaseLLM):
    """
    Простая асинхронная интеграция с OpenRouter API.
    Ожидает OPENROUTER_API_KEY в окружении или api_key в конструкторе.
    Поддерживает generate и generate_stream.
    """

    ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        model_name: str = "openai/gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 1000,  # ← ДОБАВЛЯЕМ ЭТОТ ПАРАМЕТР!
        api_key: Optional[str] = None,
        extra_headers: Optional[dict] = None,
    ):
        super().__init__(model_name, temperature)
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.max_tokens = max_tokens  # ← Сохраняем значение по умолчанию
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required for OpenRouterLLM")
        self.extra_headers = extra_headers or {}

    async def _build_headers(self):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Optional metadata (helpful for OpenRouter leaderboard)
            "X-Title": self.extra_headers.get("X-Title", "qapsula_gpt2"),
            "HTTP-Referer": self.extra_headers.get("HTTP-Referer", ""),
        }
        return headers

    async def generate(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None  # ← Делаем опциональным
    ) -> str:
        # Используем переданный max_tokens или значение по умолчанию из __init__
        tokens_to_use = max_tokens if max_tokens is not None else self.max_tokens
        
        messages = []
        messages.append({
            "role": "system",
            "content": "Ты полезный AI ассистент. Отвечай на русском языке кратко и по существу."
        })
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": float(self.temperature),
            "max_tokens": int(tokens_to_use),
            "stream": False
        }

        headers = await self._build_headers()

        async with aiohttp.ClientSession() as session:
            async with session.post(self.ENDPOINT, headers=headers, json=payload, timeout=60) as resp:
                text = await resp.text()
                if resp.status != 200:
                    return f"Ошибка при вызове OpenRouter: {resp.status} - {text}"
                try:
                    data = await resp.json()
                except Exception:
                    return f"Неправильный JSON в ответе OpenRouter: {text}"

        # Поддерживаем формат, похожий на OpenAI
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Ошибка при разборе ответа OpenRouter: {str(e)}"

    async def generate_stream(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None  # ← Делаем опциональным
    ) -> AsyncGenerator[str, None]:
        """
        Возвращает асинхронный генератор токенов / чанков.
        OpenRouter возвращает построчный стрим (каждая линия — JSON или SSE-подобная).
        """
        # Используем переданный max_tokens или значение по умолчанию из __init__
        tokens_to_use = max_tokens if max_tokens is not None else self.max_tokens
        
        messages = []
        messages.append({
            "role": "system",
            "content": "Ты полезный AI ассистент. Отвечай на русском языке кратко и по существу."
        })
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": float(self.temperature),
            "max_tokens": int(tokens_to_use),
            "stream": True
        }

        headers = await self._build_headers()

        async with aiohttp.ClientSession() as session:
            async with session.post(self.ENDPOINT, headers=headers, json=payload, timeout=None) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    yield f"Ошибка при подключении к OpenRouter: {resp.status} - {body}"
                    return

                async for raw_line in resp.content:
                    if not raw_line:
                        continue
                    try:
                        line = raw_line.decode("utf-8").strip()
                    except Exception:
                        continue
                    if not line:
                        continue
                    # иногда приходят префиксы типа 'data: ' — убираем их
                    if line.startswith("data:"):
                        line = line[len("data:"):].strip()
                        if line == "[DONE]":
                            break
                    # Попробуем распарсить JSON
                    try:
                        chunk = json.loads(line)
                        # Ожидаем структуру: choices[0].delta.content
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
                        if content:
                            yield content
                            continue
                        # Иногда приходят сразу итоговые message
                        msg = chunk.get("choices", [{}])[0].get("message", {}).get("content")
                        if msg:
                            yield msg
                            continue
                    except Exception:
                        # Если не JSON — отдаем сырую строку
                        yield line
                        continue
        return