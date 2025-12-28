from typing import List, Dict, Optional
from llama_cpp import Llama
from .llm_base import BaseLLM
import os
import asyncio
import time
import threading


class LlamaCppLLM(BaseLLM):
    """LLM реализация с llama.cpp для локальных моделей"""
    
    def __init__(
        self, 
        model_path: str,
        temperature: float = 0.7,
        n_ctx: int = 4096,
        n_gpu_layers: int = 0,  # Количество слоев на GPU (0 = только CPU)
        n_threads: int = None,  # None = авто определение
        verbose: bool = False
    ):
        super().__init__(model_path, temperature)
        
        # Автоматическое определение потоков
        if n_threads is None:
            n_threads = os.cpu_count() or 4
        
        print(f"🔧 Загрузка модели: {model_path}")
        print(f"   Контекст: {n_ctx} токенов")
        print(f"   GPU слои: {n_gpu_layers}")
        print(f"   CPU потоки: {n_threads}")
        
        try:
            self.llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                n_threads=n_threads,
                verbose=verbose
            )
            print("✅ Модель загружена успешно!")
        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            raise
    
    def _create_prompt(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: str = "Ты полезный AI ассистент. Отвечай на русском языке кратко и по существу."
    ) -> str:
        """Создать промпт в формате Llama"""
        
        # Для Llama 3 / Saiga формат
        prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
        
        # Добавляем контекст
        if context:
            for msg in context:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "user":
                    prompt += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
                elif role == "assistant":
                    prompt += f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"
        
        # Добавляем текущее сообщение
        prompt += f"<|start_header_id|>user<|end_header_id|>\n\n{message}<|eot_id|>"
        prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        
        return prompt
    
    def _generate_sync(self, full_prompt: str, max_tokens: int) -> str:
        """Синхронная генерация (для запуска в отдельном потоке)"""
        thread_id = threading.current_thread().name
        print(f"🔧 LLM._generate_sync: запущен в потоке {thread_id}")
        print(f"📊 LLM._generate_sync: параметры генерации:")
        print(f"   - max_tokens: {max_tokens}")
        print(f"   - temperature: {self.temperature}")
        print(f"   - длина промпта: {len(full_prompt)} символов")

        start_time = time.time()

        try:
            print(f"⚡ LLM._generate_sync: вызов self.llm()...")
            response = self.llm(
                full_prompt,
                max_tokens=max_tokens,
                temperature=self.temperature,
                top_p=0.95,
                top_k=40,
                repeat_penalty=1.1,
                stop=["<|eot_id|>", "<|end_of_text|>"],
                echo=False
            )

            elapsed = time.time() - start_time
            print(f"✅ LLM._generate_sync: self.llm() завершен за {elapsed:.2f} сек")

            answer = response['choices'][0]['text'].strip()
            print(f"📝 LLM._generate_sync: извлечен ответ ({len(answer)} символов)")
            return answer

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ LLM._generate_sync: ОШИБКА после {elapsed:.2f} сек")
            print(f"❌ Тип ошибки: {type(e).__name__}")
            print(f"❌ Сообщение: {str(e)}")
            import traceback
            print(f"❌ Traceback:\n{traceback.format_exc()}")
            raise

    async def generate(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 1000
    ) -> str:
        """Генерация ответа"""

        print(f"🧠 LLM: создание промпта...")
        # Создаем полный промпт с контекстом
        full_prompt = self._create_prompt(prompt, context)

        print(f"🧠 LLM: промпт создан ({len(full_prompt)} символов)")
        print(f"🧠 LLM: начало генерации (max_tokens={max_tokens})...")

        try:
            # Запускаем синхронную генерацию в отдельном потоке
            answer = await asyncio.to_thread(
                self._generate_sync,
                full_prompt,
                max_tokens
            )

            print(f"🧠 LLM: генерация завершена")
            print(f"🧠 LLM: ответ извлечен ({len(answer)} символов)")
            return answer

        except Exception as e:
            print(f"❌ LLM: ошибка при генерации: {e}")
            return f"Ошибка при генерации: {str(e)}"
    
    async def generate_stream(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 1000
    ):
        """Генерация с потоковой передачей"""
        
        full_prompt = self._create_prompt(prompt, context)
        
        try:
            stream = self.llm(
                full_prompt,
                max_tokens=max_tokens,
                temperature=self.temperature,
                top_p=0.95,
                top_k=40,
                repeat_penalty=1.1,
                stop=["<|eot_id|>", "<|end_of_text|>"],
                stream=True,
                echo=False
            )
            
            for chunk in stream:
                if chunk and 'choices' in chunk:
                    text = chunk['choices'][0].get('text', '')
                    if text:
                        yield text
                        
        except Exception as e:
            yield f"Ошибка: {str(e)}"


class MistralLlamaCppLLM(LlamaCppLLM):
    """Специализированный класс для Mistral моделей"""
    
    def _create_prompt(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: str = "Ты полезный AI ассистент. Отвечай на русском языке кратко и по существу."
    ) -> str:
        """Промпт в формате Mistral/Mixtral"""
        
        prompt = f"<s>[INST] {system_prompt}\n\n"
        
        # Добавляем контекст
        if context:
            for msg in context:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "user":
                    prompt += f"{content} [/INST]"
                elif role == "assistant":
                    prompt += f"{content}</s>[INST] "
        
        # Текущее сообщение
        prompt += f"{message} [/INST]"
        
        return prompt


class SaigaLlamaCppLLM(LlamaCppLLM):
    """Специализированный класс для русскоязычных моделей Saiga"""
    
    def _create_prompt(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: str = "Ты — Сайга, русскоязычный автоматический ассистент. Ты разговариваешь с людьми и помогаешь им."
    ) -> str:
        """Промпт для Saiga моделей"""
        
        # Формат для Saiga Llama 3
        prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
        
        if context:
            for msg in context:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "user":
                    prompt += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
                elif role == "assistant":
                    prompt += f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"
        
        prompt += f"<|start_header_id|>user<|end_header_id|>\n\n{message}<|eot_id|>"
        prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        
        return prompt
