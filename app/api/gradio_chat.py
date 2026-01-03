"""
Gradio ChatInterface для взаимодействия с OpenAI LLM.
Монтируется как отдельный эндпоинт в FastAPI приложении.
"""
import os
import gradio as gr
from openai import OpenAI

# Инициализация OpenAI клиента
client = None


def get_openai_client() -> OpenAI:
    """Получить или создать OpenAI клиент."""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")
        client = OpenAI(api_key=api_key)
    return client


def chat_with_gpt(message: str, history: list) -> str:
    """
    Обработчик сообщений для Gradio ChatInterface.

    Args:
        message: Текущее сообщение пользователя
        history: История диалога в формате [[user, assistant], ...]

    Returns:
        Ответ от GPT модели
    """
    try:
        openai_client = get_openai_client()

        # Формируем историю сообщений для API
        messages = [
            {"role": "system", "content": "Ты полезный ассистент. Отвечай на русском языке."}
        ]

        # Добавляем историю диалога
        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            if assistant_msg:
                messages.append({"role": "assistant", "content": assistant_msg})

        # Добавляем текущее сообщение
        messages.append({"role": "user", "content": message})

        # Запрос к OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Ошибка: {str(e)}"


def create_gradio_app():
    """
    Создать Gradio приложение с ChatInterface.

    Returns:
        Gradio ChatInterface с включённой очередью
    """
    demo = gr.ChatInterface(
        fn=chat_with_gpt,
        examples=[
            "Привет! Расскажи о себе.",
            "Что такое машинное обучение?",
            "Напиши простой пример на Python",
        ],
        title="🤖 Qapsula AI Chat",
        description="Чат с GPT-4.1-nano. Задавайте вопросы на любом языке.",
    )

    # Включаем очередь для WebSocket соединений
    demo.queue()

    return demo


# Создаём экземпляр приложения для монтирования
gradio_app = create_gradio_app()
