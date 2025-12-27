import os
import asyncio
from dotenv import load_dotenv
from pathlib import Path

# Импорты модулей
from app.llm.openai import OpenAILLM
from app.llm.llamacpp import LlamaCppLLM, SaigaLlamaCppLLM, MistralLlamaCppLLM
from app.vectorstore.faiss import FAISSVectorStore
from app.rag.ingest import DocumentIngestor
from app.rag.retriever import Retriever
from app.rag.generator import Generator
from app.rag.pipeline import RAGPipeline
from app.api.telegram import TelegramBot


async def initialize_vectorstore():
    """Инициализация векторного хранилища"""
    vectorstore = FAISSVectorStore()
    
    # Путь к векторному хранилищу
    vector_store_path = os.getenv("VECTOR_STORE_PATH", "./data/vectorstore")
    
    # Пытаемся загрузить существующее хранилище
    if os.path.exists(f"{vector_store_path}.index"):
        print("📂 Загрузка существующего векторного хранилища...")
        await vectorstore.load(vector_store_path)
        print(f"✓ Загружено {vectorstore.index.ntotal} векторов")
    else:
        print("🆕 Создание нового векторного хранилища...")
        
        # Загружаем документы из директории, если она существует
        documents_path = os.getenv("DOCUMENTS_PATH", "./data/documents")
        
        if os.path.exists(documents_path):
            ingestor = DocumentIngestor(vectorstore)
            total_chunks = await ingestor.ingest_directory(
                documents_path,
                extensions=['.txt', '.md']
            )
            print(f"✓ Загружено {total_chunks} чанков из {documents_path}")
            
            # Сохраняем векторное хранилище
            await vectorstore.save(vector_store_path)
            print(f"✓ Векторное хранилище сохранено в {vector_store_path}")
        else:
            print(f"⚠ Директория с документами не найдена: {documents_path}")
            print("Бот будет работать без RAG контекста")
    
    return vectorstore


async def main():
    """Главная функция"""
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем наличие необходимых токенов
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not telegram_token:
        raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env файле")
    
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY не найден в .env файле")
    
    print("🚀 Инициализация бота...")
    
    # Инициализируем компоненты
    print("🤖 Инициализация LLM...")
    
    # Выбор LLM: OpenAI или локальная модель
    use_local_model = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"
    
    if use_local_model:
        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/saiga_llama3_8b.Q4_K_M.gguf")
        model_type = os.getenv("MODEL_TYPE", "saiga")  # saiga, mistral, llama
        
        print(f"📁 Используется локальная модель: {model_path}")
        
        if model_type == "saiga":
            llm = SaigaLlamaCppLLM(
                model_path=model_path,
                temperature=0.7,
                n_ctx=4096,
                n_gpu_layers=0  # Увеличьте если есть GPU
            )
        elif model_type == "mistral":
            llm = MistralLlamaCppLLM(
                model_path=model_path,
                temperature=0.7,
                n_ctx=4096,
                n_gpu_layers=0
            )
        else:
            llm = LlamaCppLLM(
                model_path=model_path,
                temperature=0.7,
                n_ctx=4096,
                n_gpu_layers=0
            )
    else:
        print("☁️  Используется OpenAI API")
        llm = OpenAILLM(model_name="gpt-4-turbo-preview", temperature=0.7)
    
    print("📊 Инициализация векторного хранилища...")
    vectorstore = await initialize_vectorstore()
    
    print("🔍 Настройка RAG pipeline...")
    retriever = Retriever(vectorstore, top_k=3)
    generator = Generator(llm)
    rag_pipeline = RAGPipeline(
        retriever=retriever,
        generator=generator,
        use_rag_threshold=0.5
    )
    
    print("💬 Настройка Telegram бота...")
    bot = TelegramBot(token=telegram_token, rag_pipeline=rag_pipeline)
    bot.setup()
    
    print("=" * 50)
    print("✅ Все компоненты инициализированы успешно!")
    print("=" * 50)
    
    # Запускаем бота
    bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise
