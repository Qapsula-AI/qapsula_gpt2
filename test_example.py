"""
Скрипт для тестирования RAG системы без Telegram бота
"""
import asyncio
import os
from dotenv import load_dotenv

from app.llm.openai import OpenAILLM
from app.vectorstore.faiss import FAISSVectorStore
from app.rag.ingest import DocumentIngestor
from app.rag.retriever import Retriever
from app.rag.generator import Generator
from app.rag.pipeline import RAGPipeline


async def test_rag():
    """Тестирование RAG системы"""
    
    # Загружаем переменные окружения
    load_dotenv()
    
    print("🧪 Тестирование RAG системы")
    print("=" * 50)
    
    # Инициализация компонентов
    print("\n1️⃣ Инициализация LLM...")
    llm = OpenAILLM(model_name="gpt-4-turbo-preview")
    print("✓ LLM инициализирован")
    
    print("\n2️⃣ Создание векторного хранилища...")
    vectorstore = FAISSVectorStore()
    print("✓ Векторное хранилище создано")
    
    print("\n3️⃣ Загрузка тестовых документов...")
    ingestor = DocumentIngestor(vectorstore)
    
    # Тестовые документы
    test_docs = [
        {
            "text": """
            Машинное обучение (Machine Learning) — это раздел искусственного интеллекта,
            который позволяет компьютерам обучаться на данных без явного программирования.
            Основные типы машинного обучения: обучение с учителем, без учителя и обучение
            с подкреплением.
            """,
            "metadata": {"source": "ml_basics.txt"}
        },
        {
            "text": """
            Python — высокоуровневый язык программирования общего назначения.
            Python поддерживает структурное, объектно-ориентированное и функциональное
            программирование. Язык имеет динамическую типизацию и автоматическое
            управление памятью.
            """,
            "metadata": {"source": "python_basics.txt"}
        },
        {
            "text": """
            Нейронные сети — это вычислительные модели, вдохновленные биологическими
            нейронными сетями. Они состоят из слоев искусственных нейронов.
            Глубокие нейронные сети (Deep Learning) содержат множество скрытых слоев
            и способны решать сложные задачи.
            """,
            "metadata": {"source": "neural_networks.txt"}
        }
    ]
    
    for doc in test_docs:
        await ingestor.ingest_text(doc["text"], doc["metadata"])
    
    print(f"✓ Загружено {len(test_docs)} документов")
    
    print("\n4️⃣ Настройка RAG pipeline...")
    retriever = Retriever(vectorstore, top_k=2)
    generator = Generator(llm)
    rag_pipeline = RAGPipeline(retriever, generator, use_rag_threshold=0.3)
    print("✓ RAG pipeline настроен")
    
    # Тестовые запросы
    test_queries = [
        "Что такое машинное обучение?",
        "Расскажи про Python",
        "Что такое нейронные сети?",
        "Какая погода на Марсе?"  # Вопрос вне контекста
    ]
    
    print("\n5️⃣ Тестирование запросов:")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Запрос {i}: {query}")
        print("-" * 50)
        
        response = await rag_pipeline.query(query, use_rag=True, top_k=2)
        
        print(f"💬 Ответ: {response.answer}")
        
        if response.sources:
            print(f"📚 Источники: {', '.join(response.sources)}")
            print(f"🎯 Уверенность: {response.confidence:.2f}")
        else:
            print("ℹ️  Ответ без использования RAG (контекст не найден)")
        
        print()
    
    print("=" * 50)
    print("✅ Тестирование завершено!")
    
    # Сохранение векторного хранилища
    print("\n6️⃣ Сохранение векторного хранилища...")
    await vectorstore.save("./data/test_vectorstore")
    print("✓ Векторное хранилище сохранено")


async def test_without_documents():
    """Тест без загрузки документов (только GPT)"""
    
    load_dotenv()
    
    print("\n🧪 Тестирование без документов (только GPT)")
    print("=" * 50)
    
    llm = OpenAILLM(model_name="gpt-4-turbo-preview")
    vectorstore = FAISSVectorStore()
    
    retriever = Retriever(vectorstore, top_k=2)
    generator = Generator(llm)
    rag_pipeline = RAGPipeline(retriever, generator)
    
    query = "Привет! Как дела?"
    print(f"\n📝 Запрос: {query}")
    
    response = await rag_pipeline.query(query, use_rag=True)
    print(f"💬 Ответ: {response.answer}")
    
    print("\n✅ Тест завершен!")


if __name__ == "__main__":
    print("Выберите тест:")
    print("1. Полный тест с документами")
    print("2. Тест без документов (только GPT)")
    
    choice = input("\nВаш выбор (1/2): ").strip()
    
    if choice == "1":
        asyncio.run(test_rag())
    elif choice == "2":
        asyncio.run(test_without_documents())
    else:
        print("Неверный выбор. Запускаю полный тест...")
        asyncio.run(test_rag())
