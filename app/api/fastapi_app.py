"""
FastAPI приложение с мультитенантностью.
Поддерживает работу с множественными клиентами через заголовок X-Tenant-Id.
"""
from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os

from app.core.rag_manager import RAGManager
from app.rag.rag_pipeline import RAGPipeline

# Инициализация FastAPI
app = FastAPI(
    title="Multi-Tenant RAG Bot API",
    description="API для управления множественными RAG ботами с изолированными базами знаний",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
    use_rag: bool = True
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Ответ чата."""
    response: str
    tenant_id: str
    sources: Optional[List[dict]] = None


class DocumentUpload(BaseModel):
    """Загрузка документа."""
    content: str
    title: str
    metadata: Optional[dict] = None


class TenantConfig(BaseModel):
    """Конфигурация клиента."""
    llm_type: str = "openrouter"
    model: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    top_k: int = 3
    rag_threshold: float = 0.5
    system_prompt: Optional[str] = None


# === Dependencies ===

async def get_rag_manager() -> RAGManager:
    """Получить RAG Manager из состояния приложения."""
    if not hasattr(app.state, 'rag_manager'):
        raise HTTPException(
            status_code=503,
            detail="RAG Manager не инициализирован"
        )
    return app.state.rag_manager


async def get_tenant_id(
    x_tenant_id: Optional[str] = Header(
        None,
        description="ID клиента (например: client1, client2)"
    )
) -> str:
    """
    Извлечение tenant_id из заголовка.
    
    Использование:
    curl -H "X-Tenant-Id: client1" http://localhost:8000/chat
    """
    if not x_tenant_id:
        # Можно использовать дефолтного клиента
        return "default"
    
    return x_tenant_id.lower()


async def get_rag_pipeline(
    tenant_id: str = Depends(get_tenant_id),
    rag_manager: RAGManager = Depends(get_rag_manager)
) -> RAGPipeline:
    """Получить RAG pipeline для клиента."""
    pipeline = rag_manager.get_pipeline(tenant_id)
    
    if not pipeline:
        # Попытка автоматической инициализации
        try:
            print(f"⚙️  Автоинициализация RAG для {tenant_id}")
            pipeline = await rag_manager.initialize_tenant(tenant_id)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"RAG для клиента '{tenant_id}' не найден и не может быть инициализирован: {str(e)}"
            )
    
    return pipeline


# === Endpoints ===

@app.get("/", tags=["General"])
async def root(rag_manager: RAGManager = Depends(get_rag_manager)):
    """Корневой эндпоинт с информацией об API."""
    return {
        "message": "Multi-Tenant RAG Bot API",
        "version": "2.0.0",
        "active_tenants": rag_manager.list_tenants(),
        "total_tenants": len(rag_manager.list_tenants()),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "chat": "POST /chat",
            "tenants": "GET /tenants"
        }
    }


@app.get("/health", tags=["General"])
async def health_check(rag_manager: RAGManager = Depends(get_rag_manager)):
    """Проверка здоровья сервиса."""
    return {
        "status": "healthy",
        "tenants_active": len(rag_manager.list_tenants()),
        "tenants": rag_manager.list_tenants()
    }


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Отправить сообщение боту конкретного клиента.
    
    **Требуется заголовок:** `X-Tenant-Id: client1`
    
    **Пример запроса:**
    ```bash
    curl -X POST http://localhost:8000/chat \
      -H "Content-Type: application/json" \
      -H "X-Tenant-Id: client1" \
      -d '{"message": "Привет, как дела?"}'
    ```
    """
    try:
        print(f"💬 [{tenant_id}] Запрос: {request.message[:100]}...")
        
        # Генерируем ответ
        if request.use_rag:
            response = await pipeline.process_query(
                query=request.message,
                chat_history=[]  # Можно добавить историю из БД
            )
        else:
            # Прямой запрос к LLM без RAG
            llm = pipeline.generator.llm
            response = await llm.generate(request.message)
        
        print(f"✅ [{tenant_id}] Ответ отправлен")
        
        return ChatResponse(
            response=response,
            tenant_id=tenant_id,
            sources=None  # TODO: добавить источники из retriever
        )
    
    except Exception as e:
        print(f"❌ [{tenant_id}] Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/upload", tags=["Documents"])
async def upload_document(
    doc: DocumentUpload,
    background_tasks: BackgroundTasks,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
    tenant_id: str = Depends(get_tenant_id),
    rag_manager: RAGManager = Depends(get_rag_manager)
):
    """
    Загрузить документ в векторное хранилище клиента.
    
    **Требуется заголовок:** `X-Tenant-Id: client1`
    
    **Пример:**
    ```bash
    curl -X POST http://localhost:8000/documents/upload \
      -H "Content-Type: application/json" \
      -H "X-Tenant-Id: client1" \
      -d '{
        "title": "FAQ",
        "content": "Q: Что это? A: Документ",
        "metadata": {"author": "Admin"}
      }'
    ```
    """
    try:
        from app.schemas import Document
        from app.rag.rag_ingest import DocumentIngestor
        from pathlib import Path
        import os
        
        # Создаём документ
        document = Document(
            content=doc.content,
            metadata={
                "title": doc.title,
                "source": "api_upload",
                "tenant_id": tenant_id,
                **(doc.metadata or {})
            }
        )
        
        # Получаем векторное хранилище
        vectorstore = rag_manager.get_vectorstore(tenant_id)
        if not vectorstore:
            raise HTTPException(
                status_code=500,
                detail=f"Векторное хранилище для {tenant_id} не найдено"
            )
        
        # Индексируем в фоне
        async def ingest_task():
            ingestor = DocumentIngestor(vectorstore)
            chunks = await ingestor.ingest_document(document)
            
            # Сохраняем обновлённое хранилище
            base_data_dir = Path(os.getenv("DATA_DIR", "./data"))
            vectorstore_path = base_data_dir / tenant_id / "vectorstore"
            await vectorstore.save(str(vectorstore_path))
            
            print(f"✅ [{tenant_id}] Документ '{doc.title}' проиндексирован ({chunks} чанков)")
            return chunks
        
        background_tasks.add_task(ingest_task)
        
        return {
            "status": "processing",
            "tenant_id": tenant_id,
            "message": f"Документ '{doc.title}' добавлен в очередь индексации"
        }
    
    except Exception as e:
        print(f"❌ [{tenant_id}] Ошибка загрузки документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/search", tags=["Documents"])
async def search_documents(
    query: str,
    k: int = 3,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Поиск релевантных документов в базе знаний клиента.
    
    **Требуется заголовок:** `X-Tenant-Id: client1`
    
    **Пример:**
    ```bash
    curl "http://localhost:8000/documents/search?query=продукт&k=5" \
      -H "X-Tenant-Id: client1"
    ```
    """
    try:
        print(f"🔍 [{tenant_id}] Поиск: {query}")
        
        results = await pipeline.retriever.retrieve(query, k=k)
        
        return {
            "query": query,
            "tenant_id": tenant_id,
            "count": len(results),
            "results": [
                {
                    "content": doc.content[:200] + "...",  # Первые 200 символов
                    "metadata": doc.metadata
                }
                for doc in results
            ]
        }
    
    except Exception as e:
        print(f"❌ [{tenant_id}] Ошибка поиска: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tenants", tags=["Tenants"])
async def list_tenants(rag_manager: RAGManager = Depends(get_rag_manager)):
    """Список всех активных клиентов."""
    stats = rag_manager.get_stats()
    
    return {
        "total": stats['total_tenants'],
        "tenants": [
            {
                "id": tenant_id,
                **tenant_data
            }
            for tenant_id, tenant_data in stats['tenants'].items()
        ]
    }


@app.post("/tenants/{tenant_id}/initialize", tags=["Tenants"])
async def initialize_tenant(
    tenant_id: str,
    config: Optional[TenantConfig] = None,
    rag_manager: RAGManager = Depends(get_rag_manager)
):
    """
    Инициализировать RAG для нового клиента.
    
    **Пример:**
    ```bash
    curl -X POST http://localhost:8000/tenants/client1/initialize \
      -H "Content-Type: application/json" \
      -d '{
        "llm_type": "openrouter",
        "model": "openai/gpt-4o-mini",
        "system_prompt": "Ты помощник компании X"
      }'
    ```
    """
    try:
        config_dict = config.dict() if config else None
        pipeline = await rag_manager.initialize_tenant(tenant_id, config_dict)
        
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "message": f"RAG для '{tenant_id}' инициализирован"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tenants/{tenant_id}/reload", tags=["Tenants"])
async def reload_tenant(
    tenant_id: str,
    rag_manager: RAGManager = Depends(get_rag_manager)
):
    """
    Перезагрузить RAG клиента.
    Полезно после обновления документов или конфигурации.
    """
    try:
        await rag_manager.reload_tenant(tenant_id)
        
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "message": f"RAG для '{tenant_id}' перезагружен"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tenants/{tenant_id}/stats", tags=["Tenants"])
async def get_tenant_stats(
    tenant_id: str,
    rag_manager: RAGManager = Depends(get_rag_manager)
):
    """Статистика конкретного клиента."""
    pipeline = rag_manager.get_pipeline(tenant_id)
    
    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail=f"Клиент '{tenant_id}' не найден"
        )
    
    try:
        vectorstore = rag_manager.get_vectorstore(tenant_id)
        vectorstore_size = vectorstore.index.ntotal if vectorstore else 0
        
        llm = rag_manager.get_llm(tenant_id)
        llm_type = type(llm).__name__ if llm else "Unknown"
        
        return {
            "tenant_id": tenant_id,
            "status": "active",
            "vectorstore_size": vectorstore_size,
            "llm_type": llm_type,
            "top_k": pipeline.retriever.top_k,
            "rag_threshold": pipeline.use_rag_threshold
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", tags=["Statistics"])
async def get_global_stats(rag_manager: RAGManager = Depends(get_rag_manager)):
    """Глобальная статистика всех клиентов."""
    return rag_manager.get_stats()


# === События жизненного цикла ===

@app.on_event("startup")
async def startup_event():
    """Инициализация при старте FastAPI."""
    print("\n" + "="*60)
    print("🌐 FastAPI сервер запускается...")
    print("="*60)
    
    # RAG Manager будет установлен из main_app.py
    if not hasattr(app.state, 'rag_manager'):
        print("⚠️  RAG Manager не установлен, инициализация отложена")
    else:
        print(f"✅ RAG Manager подключен")
        print(f"   Активных клиентов: {len(app.state.rag_manager.list_tenants())}")
    
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке."""
    print("\n" + "="*60)
    print("🛑 FastAPI сервер останавливается...")
    print("="*60 + "\n")