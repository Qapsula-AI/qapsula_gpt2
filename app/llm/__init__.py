"""LLM модуль - интеграции с языковыми моделями"""

from .llm_base import BaseLLM
from .llm_openai import OpenAILLM
# from .llm_llamacpp import LlamaCppLLM, SaigaLlamaCppLLM, MistralLlamaCppLLM  # Локальные модели не используются
from .llm_openrouter import OpenRouterLLM

__all__ = [
    'BaseLLM',
    'OpenAILLM',
    # 'LlamaCppLLM',
    # 'SaigaLlamaCppLLM',
    # 'MistralLlamaCppLLM',
    'OpenRouterLLM',
]