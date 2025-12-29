"""
Главное приложение с поддержкой мультитенантности.
Запускает FastAPI и множественные Telegram боты параллельно.
"""
import os
import asyncio
from dotenv import load_dotenv
from pathlib import Path
import uvicorn

from app.core.rag_manager import RAGManager
from app.api.telegram_bot import TelegramBot
from app.api.fastapi_app import app as fastapi_app


# Загружаем переменные окружения
load_dotenv()


async def run_telegram_bot(token: str, tenant_id: str, rag_manager: RAGManager):
    """
    Запуск одного Telegram бота для конкретного клиента.
    
    Args:
        token: Telegram Bot Token
        tenant_id: ID клиента (например, client1, client2)
        rag_manager: Общий менеджер RAG
    """
    try:
        print(f"🤖 Запуск Telegram бота для {tenant_id}...")
        
        # Создаём инстанс бота
        bot = TelegramBot(
            token=token,
            tenant_id=tenant_id,
            rag_manager=rag_manager
        )
        
        # Инициализируем бота
        await bot.initialize()
        
        # Запускаем бота
        await bot.start()
        
        print(f"✅ Telegram бот {tenant_id} запущен успешно")
        
        # Держим бота запущенным
        await asyncio.Event().wait()
        
    except Exception as e:
        print(f"❌ Ошибка запуска бота {tenant_id}: {e}")
        raise


async def run_fastapi(rag_manager: RAGManager):
    """
    Запуск FastAPI сервера.
    
    Args:
        rag_manager: Общий менеджер RAG для всех клиентов
    """
    try:
        print("🌐 Запуск FastAPI сервера...")
        
        # Передаём RAG Manager в FastAPI приложение
        fastapi_app.state.rag_manager = rag_manager
        
        # Конфигурация Uvicorn
        config = uvicorn.Config(
            fastapi_app,
            host="0.0.0.0",
            port=int(os.getenv("API_PORT", 8000)),
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        print(f"❌ Ошибка запуска FastAPI: {e}")
        raise


async def initialize_system():
    """
    Инициализация всей системы.
    
    Returns:
        tuple: (rag_manager, bot_configs)
    """
    print("=" * 60)
    print("🚀 Инициализация Multi-Tenant системы...")
    print("=" * 60)
    
    # Создаём единственный экземпляр RAG Manager (Singleton)
    rag_manager = RAGManager()
    
    # Собираем конфигурации ботов из переменных окружения
    # Формат: TELEGRAM_BOT_<TENANT_ID>=<TOKEN>
    # Пример: TELEGRAM_BOT_CLIENT1=123456:ABC...
    #         TELEGRAM_BOT_CLIENT2=789012:DEF...
    
    bot_configs = []
    
    for key, value in os.environ.items():
        if key.startswith("TELEGRAM_BOT_"):
            # Извлекаем tenant_id из имени переменной
            tenant_id = key.replace("TELEGRAM_BOT_", "").lower()
            token = value
            
            if token and token.strip():
                print(f"📱 Найден бот для клиента: {tenant_id}")
                bot_configs.append({
                    "tenant_id": tenant_id,
                    "token": token
                })
    
    # Если не найдено ни одного бота, используем дефолтный из TELEGRAM_BOT_TOKEN
    if not bot_configs:
        default_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if default_token:
            print("📱 Используется дефолтный бот (tenant: default)")
            bot_configs.append({
                "tenant_id": "default",
                "token": default_token
            })
        else:
            print("⚠️  Telegram боты не настроены")
    
    # Автоматически инициализируем RAG для всех найденных клиентов
    # (проверяем директории в data/)
    data_dir = Path("./data")
    if data_dir.exists():
        for tenant_dir in data_dir.iterdir():
            if tenant_dir.is_dir():
                tenant_id = tenant_dir.name
                
                # Пропускаем служебные директории
                if tenant_id in ['vectorstore', 'documents', '__pycache__']:
                    continue
                
                print(f"📦 Обнаружена директория клиента: {tenant_id}")
                
                try:
                    # Инициализируем RAG для этого клиента
                    await rag_manager.initialize_tenant(tenant_id)
                except Exception as e:
                    print(f"⚠️  Ошибка инициализации RAG для {tenant_id}: {e}")
                    print(f"   RAG для {tenant_id} будет инициализирован при первом запросе")
    
    print("=" * 60)
    print(f"✅ Система инициализирована")
    print(f"   Активных клиентов: {len(rag_manager.list_tenants())}")
    print(f"   Telegram ботов: {len(bot_configs)}")
    print("=" * 60)
    
    return rag_manager, bot_configs


async def main():
    """
    Главная функция запуска системы.
    Запускает FastAPI и все Telegram боты параллельно.
    """
    try:
        # Инициализация системы
        rag_manager, bot_configs = await initialize_system()
        
        # Собираем задачи для параллельного выполнения
        tasks = []
        
        # 1. FastAPI сервер (обязательно)
        tasks.append(
            asyncio.create_task(
                run_fastapi(rag_manager),
                name="FastAPI-Server"
            )
        )
        
        # 2. Telegram боты (если есть)
        for bot_config in bot_configs:
            tasks.append(
                asyncio.create_task(
                    run_telegram_bot(
                        token=bot_config["token"],
                        tenant_id=bot_config["tenant_id"],
                        rag_manager=rag_manager
                    ),
                    name=f"TelegramBot-{bot_config['tenant_id']}"
                )
            )
        
        if not tasks:
            print("❌ Нет задач для запуска")
            return
        
        print("\n" + "=" * 60)
        print("🎯 Запуск всех сервисов...")
        print("=" * 60)
        
        for task in tasks:
            print(f"   ▶️  {task.get_name()}")
        
        print("=" * 60 + "\n")
        
        # Запускаем все задачи параллельно
        await asyncio.gather(*tasks, return_exceptions=True)
        
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("👋 Получен сигнал остановки (Ctrl+C)")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Критическая ошибка: {e}")
        print("=" * 60)
        raise
    
    finally:
        print("\n" + "=" * 60)
        print("🛑 Остановка всех сервисов...")
        print("=" * 60)


def run():
    """
    Точка входа в приложение.
    Запускается через: python -m app.main_app
    """
    try:
        # Запускаем главную асинхронную функцию
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено пользователем")
        
    except Exception as e:
        print(f"\n❌ Фатальная ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run()