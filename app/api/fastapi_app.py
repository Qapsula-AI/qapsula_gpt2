"""
FastAPI приложение с мультитенантностью.
Поддерживает работу с множественными клиентами через заголовок X-Tenant-Id.
"""
from datetime import timedelta
from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
import os

from app.core.rag_manager import RAGManager
from app.rag.rag_pipeline import RAGPipeline
from app.db.database import get_db
from app.db.models import User
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_admin,
    TokenResponse,
    UserResponse
)

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


# === Auth Endpoints ===

@app.post("/api/login", response_model=TokenResponse, tags=["Authentication"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Авторизация пользователя и получение JWT токена.

    **Использование:**
    ```bash
    curl -X POST http://localhost:8000/api/login \
      -d "username=admin&password=your_password"
    ```

    **Формат ответа:**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
    ```
    """
    # Ищем пользователя в БД
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем пароль
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем активен ли пользователь
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Пользователь деактивирован",
        )

    # Создаём JWT токен
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )

    return TokenResponse(access_token=access_token, token_type="bearer")


@app.get("/api/users/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Получить информацию о текущем авторизованном пользователе.

    **Требуется:** Authorization заголовок с Bearer токеном

    **Использование:**
    ```bash
    curl http://localhost:8000/api/users/me \
      -H "Authorization: Bearer YOUR_TOKEN"
    ```
    """
    return UserResponse.from_orm(current_user)


@app.post("/api/logout", tags=["Authentication"])
async def logout():
    """
    Выход из системы.

    Примечание: JWT токены stateless, поэтому фактический logout
    происходит на стороне клиента (удаление токена из localStorage).

    Этот endpoint существует для совместимости с фронтендом.
    """
    return {"message": "Успешный выход из системы"}


# === RAG API Endpoints ===

@app.get("/api/", tags=["General"])
async def root(
    rag_manager: RAGManager = Depends(get_rag_manager),
    current_user: User = Depends(get_current_user)
):
    """API информация (требует авторизацию)."""
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
async def list_tenants(
    current_user: User = Depends(get_current_user),
    rag_manager: RAGManager = Depends(get_rag_manager)
):
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
    current_user: User = Depends(require_admin),
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
    current_user: User = Depends(require_admin),
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
    current_user: User = Depends(get_current_user),
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
async def get_global_stats(
    current_user: User = Depends(get_current_user),
    rag_manager: RAGManager = Depends(get_rag_manager)
):
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


# === Обслуживание Vue.js фронтенда ===

# Проверяем режим разработки
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
# В Docker используем host.docker.internal для доступа к хосту
VITE_DEV_SERVER = os.getenv("VITE_DEV_SERVER", "http://host.docker.internal:5173")

if DEV_MODE:
    # Dev режим - проксируем на Vite dev server для hot reload
    import httpx

    print(f"🔥 DEV MODE: Проксирование фронтенда на {VITE_DEV_SERVER}")
    print(f"   Запустите Vite: cd app/frontend && npm run dev")

    from starlette.requests import Request
    from starlette.responses import StreamingResponse
    import httpx

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    async def proxy_to_vite(request: Request, full_path: str):
        """
        В dev режиме проксируем ВСЕ запросы на Vite dev server.
        Поддерживает GET, POST и другие методы для правильной работы HMR.
        """
        # Пропускаем API маршруты и документацию
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc"):
            raise HTTPException(status_code=404, detail="Not found")

        # Формируем URL для Vite
        url = f"{VITE_DEV_SERVER}/{full_path}"
        if request.url.query:
            url = f"{url}?{request.url.query}"

        # Проксируем запрос
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Получаем тело запроса если есть
                body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None

                # Делаем запрос к Vite БЕЗ заголовков - избегаем проблем с кодировкой
                response = await client.request(
                    method=request.method,
                    url=url,
                    content=body,
                    follow_redirects=True
                )

                # Используем StreamingResponse для прямого проксирования
                # Это избегает проблем с кодировкой
                from fastapi.responses import StreamingResponse

                # Создаем async generator для стриминга
                async def generate():
                    yield response.content

                return StreamingResponse(
                    generate(),
                    status_code=response.status_code,
                    media_type=response.headers.get("content-type", "text/html")
                )
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=503,
                    detail=f"Vite dev server не запущен. Запустите: cd app/frontend && npm run dev"
                )
            except Exception as e:
                print(f"❌ Ошибка проксирования: {e}")
                raise HTTPException(status_code=500, detail=str(e))
else:
    # Production режим - обслуживаем собранные статические файлы
    STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

    if os.path.exists(STATIC_DIR):
        # Обслуживаем статические файлы (CSS, JS, изображения)
        app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """
            SPA fallback - отдаёт index.html для всех не-API маршрутов.
            Это позволяет Vue Router работать в режиме history mode.
            """
            # Пропускаем API маршруты и документацию
            if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc"):
                raise HTTPException(status_code=404, detail="Not found")

            # Пытаемся найти конкретный файл
            file_path = os.path.join(STATIC_DIR, full_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)

            # Для всех остальных маршрутов отдаём index.html (SPA)
            index_path = os.path.join(STATIC_DIR, "index.html")
            if os.path.isfile(index_path):
                return FileResponse(index_path)

            # Если index.html не найден - 404
            raise HTTPException(
                status_code=404,
                detail="Frontend не собран. Выполните: cd app/frontend && npm run build"
            )
    else:
        print(f"⚠️  Директория {STATIC_DIR} не найдена. Фронтенд не будет обслуживаться.")
        print(f"   Для сборки фронтенда выполните: cd app/frontend && npm install && npm run build")