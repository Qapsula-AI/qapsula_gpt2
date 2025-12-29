"""
Telegram бот с поддержкой мультитенантности.
Каждый бот работает с отдельной базой знаний через RAG Manager.
"""
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from app.core.rag_manager import RAGManager


class TelegramBot:
    """Telegram бот с мультитенантностью."""
    
    def __init__(self, token: str, tenant_id: str, rag_manager: RAGManager):
        """
        Инициализация Telegram бота.
        
        Args:
            token: Telegram Bot Token
            tenant_id: ID клиента (определяет какую базу знаний использовать)
            rag_manager: Общий менеджер RAG для всех клиентов
        """
        self.token = token
        self.tenant_id = tenant_id
        self.rag_manager = rag_manager
        self.application = None
        
        print(f"🤖 Создан бот для клиента: {tenant_id}")
    
    async def initialize(self):
        """Инициализация бота и его компонентов."""
        print(f"\n{'='*60}")
        print(f"📱 Инициализация Telegram бота: {self.tenant_id}")
        print(f"{'='*60}")
        
        # Убеждаемся что RAG для этого клиента инициализирован
        pipeline = self.rag_manager.get_pipeline(self.tenant_id)
        if not pipeline:
            print(f"⚙️  RAG еще не инициализирован, инициализируем...")
            await self.rag_manager.initialize_tenant(self.tenant_id)
        else:
            print(f"✅ RAG уже инициализирован")
        
        # Создаём Telegram приложение
        self.application = Application.builder().token(self.token).build()
        
        # Регистрируем обработчики команд
        self.application.add_handler(
            CommandHandler("start", self.start_command)
        )
        self.application.add_handler(
            CommandHandler("help", self.help_command)
        )
        self.application.add_handler(
            CommandHandler("clear", self.clear_command)
        )
        self.application.add_handler(
            CommandHandler("info", self.info_command)
        )
        
        # Обработчик текстовых сообщений
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_message
            )
        )
        
        print(f"✅ Telegram бот {self.tenant_id} инициализирован")
        print(f"{'='*60}\n")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start."""
        welcome_message = (
            f"👋 Привет! Я интеллектуальный помощник.\n\n"
            f"🤖 Клиент: {self.tenant_id}\n\n"
            f"Я могу ответить на вопросы на основе базы знаний.\n"
            f"Просто напиши свой вопрос!\n\n"
            f"📝 Доступные команды:\n"
            f"/help - Показать справку\n"
            f"/info - Информация о боте\n"
            f"/clear - Очистить историю разговора"
        )
        
        await update.message.reply_text(welcome_message)
        print(f"🟢 [{self.tenant_id}] Новый пользователь: {update.effective_user.username}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help."""
        help_message = (
            f"ℹ️ Справка по боту ({self.tenant_id})\n\n"
            f"🔹 Просто напиши вопрос, и я постараюсь ответить на основе базы знаний.\n\n"
            f"📌 Команды:\n"
            f"/start - Начать работу\n"
            f"/help - Эта справка\n"
            f"/info - Информация о боте и статистика\n"
            f"/clear - Очистить историю диалога\n\n"
            f"💡 Совет: Чем конкретнее вопрос, тем точнее ответ!"
        )
        
        await update.message.reply_text(help_message)
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /clear - очистка истории."""
        # Очищаем историю пользователя из context.user_data
        if 'chat_history' in context.user_data:
            context.user_data['chat_history'] = []
        
        await update.message.reply_text(
            "🗑️ История диалога очищена!\n"
            "Можешь задать новый вопрос."
        )
        
        print(f"🔄 [{self.tenant_id}] Пользователь {update.effective_user.username} очистил историю")
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /info - информация о боте."""
        pipeline = self.rag_manager.get_pipeline(self.tenant_id)
        
        if not pipeline:
            await update.message.reply_text("⚠️ RAG не инициализирован")
            return
        
        try:
            # Получаем статистику векторного хранилища
            vectorstore_size = pipeline.retriever.vectorstore.index.ntotal
            
            # Получаем информацию о LLM
            llm = self.rag_manager.get_llm(self.tenant_id)
            llm_type = type(llm).__name__
            
            info_message = (
                f"ℹ️ Информация о боте\n\n"
                f"🏢 Клиент: {self.tenant_id}\n"
                f"🤖 LLM: {llm_type}\n"
                f"📊 Документов в базе: {vectorstore_size}\n"
                f"🔍 Top-K поиска: {pipeline.retriever.top_k}\n"
                f"⚖️ RAG порог: {pipeline.use_rag_threshold}\n\n"
                f"✅ Бот работает нормально"
            )
        except Exception as e:
            info_message = (
                f"ℹ️ Информация о боте\n\n"
                f"🏢 Клиент: {self.tenant_id}\n"
                f"⚠️ Ошибка получения статистики: {str(e)}"
            )
        
        await update.message.reply_text(info_message)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений от пользователя."""
        user_message = update.message.text
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        print(f"📩 [{self.tenant_id}] Сообщение от {username}: {user_message[:50]}...")
        
        # Показываем индикатор печатания
        await update.message.chat.send_action(action="typing")
        
        # Получаем RAG pipeline
        pipeline = self.rag_manager.get_pipeline(self.tenant_id)
        
        if not pipeline:
            await update.message.reply_text(
                "⚠️ RAG не инициализирован. Попробуйте позже."
            )
            print(f"❌ [{self.tenant_id}] RAG не инициализирован")
            return
        
        try:
            # Получаем историю чата из context.user_data
            if 'chat_history' not in context.user_data:
                context.user_data['chat_history'] = []
            
            chat_history = context.user_data['chat_history']
            
            # Ограничиваем историю последними 10 сообщениями
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
            
            print(f"🔄 [{self.tenant_id}] Обработка запроса...")
            
            # Генерируем ответ через RAG Pipeline
            response = await pipeline.process_query(
                query=user_message,
                chat_history=chat_history
            )
            
            # Отправляем ответ пользователю
            await update.message.reply_text(response)
            
            # Обновляем историю
            chat_history.append({
                "role": "user",
                "content": user_message
            })
            chat_history.append({
                "role": "assistant",
                "content": response
            })
            
            context.user_data['chat_history'] = chat_history
            
            print(f"✅ [{self.tenant_id}] Ответ отправлен пользователю {username}")
        
        except Exception as e:
            error_message = f"❌ Произошла ошибка при обработке запроса: {str(e)}"
            await update.message.reply_text(error_message)
            
            print(f"❌ [{self.tenant_id}] Ошибка: {e}")
            import traceback
            traceback.print_exc()
    
    async def start(self):
        """Запуск бота (polling)."""
        if not self.application:
            raise RuntimeError("Бот не инициализирован. Вызовите initialize() сначала.")
        
        print(f"🚀 Запуск polling для бота {self.tenant_id}...")
        
        # Инициализируем приложение
        await self.application.initialize()
        await self.application.start()
        
        # Запускаем polling
        await self.application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
        print(f"✅ Бот {self.tenant_id} успешно запущен и работает")
    
    async def stop(self):
        """Остановка бота."""
        if self.application:
            print(f"🛑 Остановка бота {self.tenant_id}...")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            print(f"✅ Бот {self.tenant_id} остановлен")