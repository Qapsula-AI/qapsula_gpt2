"""FastAPI приложение для веб-интерфейса и API."""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio

from app.rag.rag_pipeline import RAGPipeline
from app.llm.llm_openrouter import OpenRouterLLM


# Инициализация FastAPI
app = FastAPI(
    title="Telegram RAG Bot API",
    description="API для управления RAG ботом",
    version="1.0.0"
)

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Pydantic модели ===

class ChatRequest(BaseModel):
    """Запрос чата."""
    message: str
    user_id: Optional[str] = "api_user"
    use_rag: bool = True


class ChatResponse(BaseModel):
    """Ответ чата."""
    response: str
    sources: Optional[List[str]] = None
    tokens_used: Optional[int] = None


class DocumentUpload(BaseModel):
    """Загрузка документа."""
    content: str
    title: str
    metadata: Optional[dict] = None


class HealthResponse(BaseModel):
    """Статус здоровья."""
    status: str
    version: str
    vectorstore_size: int


# === Глобальные объекты (инициализируются при старте) ===
rag_pipeline: Optional[RAGPipeline] = None
llm: Optional[OpenRouterLLM] = None


# === Эндпоинты ===

@app.get("/", tags=["General"])
async def root():
    """Корневой эндпоинт."""
    return {
        "message": "Telegram RAG Bot API",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Проверка здоровья сервиса."""
    vectorstore_size = 0
    if rag_pipeline and rag_pipeline.retriever:
        try:
            vectorstore_size = rag_pipeline.retriever.vectorstore.index.ntotal
        except:
            pass
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "vectorstore_size": vectorstore_size
    }


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Отправить сообщение боту и получить ответ.
    
    - **message**: Текст сообщения
    - **user_id**: ID пользователя (опционально)
    - **use_rag**: Использовать RAG или нет
    """
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    try:
        # Генерируем ответ
        if request.use_rag:
            response = await rag_pipeline.process_query(
                query=request.message,
                chat_history=[]  # Можно добавить историю
            )
        else:
            # Прямой запрос к LLM без RAG
            response = await llm.generate(request.message)
        
        return {
            "response": response,
            "sources": None,  # Можно добавить источники
            "tokens_used": None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/upload", tags=["Documents"])
async def upload_document(doc: DocumentUpload, background_tasks: BackgroundTasks):
    """
    Загрузить документ в векторное хранилище.
    
    - **content**: Текст документа
    - **title**: Название документа
    - **metadata**: Дополнительные метаданные
    """
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    try:
        from app.schemas import Document
        from app.rag.rag_ingest import DocumentIngestor
        
        # Создаём документ
        document = Document(
            content=doc.content,
            metadata={
                "title": doc.title,
                "source": "api_upload",
                **(doc.metadata or {})
            }
        )
        
        # Загружаем в фоне
        ingestor = DocumentIngestor(rag_pipeline.retriever.vectorstore)
        
        async def ingest_task():
            chunks = await ingestor.ingest_document(document)
            # Сохраняем обновлённое хранилище
            import os
            vector_store_path = os.getenv("VECTOR_STORE_PATH", "./data/vectorstore")
            await rag_pipeline.retriever.vectorstore.save(vector_store_path)
            return chunks
        
        background_tasks.add_task(ingest_task)
        
        return {
            "status": "processing",
            "message": f"Документ '{doc.title}' добавлен в очередь загрузки"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/search", tags=["Documents"])
async def search_documents(query: str, k: int = 3):
    """
    Поиск релевантных документов.
    
    - **query**: Поисковый запрос
    - **k**: Количество результатов
    """
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    try:
        results = await rag_pipeline.retriever.retrieve(query, k=k)
        
        return {
            "query": query,
            "results": [
                {
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "score": doc.metadata.get("score", 0)
                }
                for doc in results
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", tags=["Statistics"])
async def get_statistics():
    """Получить статистику бота."""
    vectorstore_size = 0
    if rag_pipeline and rag_pipeline.retriever:
        try:
            vectorstore_size = rag_pipeline.retriever.vectorstore.index.ntotal
        except:
            pass
    
    return {
        "vectorstore": {
            "total_vectors": vectorstore_size,
            "model": "sentence-transformers/all-MiniLM-L6-v2"
        },
        "llm": {
            "provider": "OpenRouter",
            "model": "openai/gpt-4o-mini"
        }
    }


# === События жизненного цикла ===

@app.on_event("startup")
async def startup_event():
    """Инициализация при старте."""
    global rag_pipeline, llm
    
    print("🚀 Запуск FastAPI сервера...")
    
    # Здесь можно инициализировать RAG pipeline
    # (или получить из существующего main_app.py)
    
    print("✅ FastAPI сервер готов")


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке."""
    print("👋 Остановка FastAPI сервера...")