import os
from typing import Dict
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from ..schemas import ChatHistory
from ..rag.rag_pipeline import RAGPipeline


class TelegramBot:
    """Telegram бот с RAG"""
    
    def __init__(self, token: str, rag_pipeline: RAGPipeline):
        self.token = token
        self.rag_pipeline = rag_pipeline
        self.chat_histories: Dict[int, ChatHistory] = {}
        self.application = None
    
    def _get_chat_history(self, user_id: int) -> ChatHistory:
        """Получить историю чата для пользователя"""
        if user_id not in self.chat_histories:
            self.chat_histories[user_id] = ChatHistory(user_id=user_id)
        return self.chat_histories[user_id]
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n\n"
            "Я AI ассистент с RAG архитектурой.\n"
            "Задавай мне любые вопросы!\n\n"
            "Команды:\n"
            "/start - Начать\n"
            "/clear - Очистить историю\n"
            "/help - Помощь"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        await update.message.reply_text(
            "📚 Доступные команды:\n\n"
            "/start - Начать работу с ботом\n"
            "/clear - Очистить историю разговора\n"
            "/help - Показать эту справку\n\n"
            "Просто напиши мне свой вопрос, и я постараюсь помочь!"
        )
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /clear"""
        user_id = update.effective_user.id
        if user_id in self.chat_histories:
            self.chat_histories[user_id] = ChatHistory(user_id=user_id)
        await update.message.reply_text("✅ История очищена!")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        message_text = update.message.text

        print(f"📩 Получено сообщение от {user_id}: {message_text}")

        # Получаем историю чата
        chat_history = self._get_chat_history(user_id)

        # Добавляем сообщение пользователя в историю
        chat_history.add_message("user", message_text)

        # Показываем, что бот печатает
        await update.message.chat.send_action(action="typing")

        print(f"🔄 Обработка запроса...")

        try:
            # Получаем контекст для LLM (последние 10 сообщений)
            context_messages = chat_history.get_context(max_messages=10)
            
            # Получаем ответ от RAG pipeline
            response = await self.rag_pipeline.query(
                question=message_text,
                chat_history=context_messages[:-1],  # Исключаем последнее сообщение (текущее)
                use_rag=True,
                top_k=3
            )

            print(f"✅ Ответ получен от LLM")

            answer = response.answer

            # Добавляем информацию об источниках, если они есть
            if response.sources:
                answer += f"\n\n📚 Источники: {', '.join(response.sources)}"

            # Добавляем ответ в историю
            chat_history.add_message("assistant", answer)

            # Отправляем ответ
            await update.message.reply_text(answer)

            print(f"📤 Ответ отправлен пользователю")
            
        except Exception as e:
            error_message = f"Произошла ошибка: {str(e)}"
            await update.message.reply_text(error_message)
            print(f"Error: {e}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        print(f"Update {update} caused error {context.error}")
    
    def setup(self):
        """Настроить бота"""
        self.application = Application.builder().token(self.token).build()
        
        # Регистрируем обработчики
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("clear", self.clear_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        # Регистрируем обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
    def run(self):
        """Запустить бота"""
        if not self.application:
            self.setup()
        
        print("🤖 Бот запущен!")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
