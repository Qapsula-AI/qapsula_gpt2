"""
Менеджер для управления множественными RAG инстансами.
Поддерживает мультитенантность - каждый клиент имеет свою базу знаний и настройки.
"""
import os
from typing import Dict, Optional
from pathlib import Path
import yaml

from app.rag.rag_pipeline import RAGPipeline
from app.rag.rag_retriever import Retriever
from app.rag.rag_generator import Generator
from app.rag.rag_ingest import DocumentIngestor
from app.vectorstore.vectorstore_faiss import FAISSVectorStore
from app.llm.llm_openrouter import OpenRouterLLM
from app.llm.llm_openai import OpenAILLM
from app.llm.llm_llamacpp import LlamaCppLLM, SaigaLlamaCppLLM, MistralLlamaCppLLM


class RAGManager:
    """
    Менеджер RAG инстансов для мультитенантности.
    Singleton - создаётся только один экземпляр для всего приложения.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - только один экземпляр."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Инициализация менеджера."""
        if self._initialized:
            return
        
        self._pipelines: Dict[str, RAGPipeline] = {}
        self._llms: Dict[str, any] = {}
        self._vectorstores: Dict[str, FAISSVectorStore] = {}
        self._initialized = True
        
        print("🔧 RAG Manager инициализирован")
    
    async def initialize_tenant(
        self,
        tenant_id: str,
        config: Optional[dict] = None,
        force_reload: bool = False
    ) -> RAGPipeline:
        """
        Инициализация RAG pipeline для конкретного клиента.
        
        Args:
            tenant_id: ID клиента (client1, client2, default, etc.)
            config: Конфигурация клиента (если None, загружается из файла)
            force_reload: Принудительная перезагрузка
        
        Returns:
            RAGPipeline для этого клиента
        """
        # Если уже инициализирован и не требуется перезагрузка
        if tenant_id in self._pipelines and not force_reload:
            print(f"✅ RAG для '{tenant_id}' уже инициализирован")
            return self._pipelines[tenant_id]
        
        print(f"\n{'='*60}")
        print(f"🚀 Инициализация RAG для клиента: {tenant_id}")
        print(f"{'='*60}")
        
        # Загружаем конфигурацию
        if config is None:
            config = self._load_tenant_config(tenant_id)
        
        # Определяем пути к данным клиента
        base_data_dir = Path(os.getenv("DATA_DIR", "./data"))
        tenant_data_dir = base_data_dir / tenant_id
        documents_path = tenant_data_dir / "documents"
        vectorstore_path = tenant_data_dir / "vectorstore"
        
        # Создаём директории если не существуют
        documents_path.mkdir(parents=True, exist_ok=True)
        vectorstore_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Директория данных: {tenant_data_dir}")
        print(f"📄 Документы: {documents_path}")
        print(f"💾 Векторное хранилище: {vectorstore_path}")
        
        # 1. Инициализация LLM
        llm = await self._initialize_llm(tenant_id, config)
        self._llms[tenant_id] = llm
        
        # 2. Инициализация векторного хранилища
        vectorstore = await self._initialize_vectorstore(
            tenant_id=tenant_id,
            documents_path=documents_path,
            vectorstore_path=vectorstore_path
        )
        self._vectorstores[tenant_id] = vectorstore
        
        # 3. Создание RAG Pipeline
        retriever = Retriever(
            vectorstore=vectorstore,
            top_k=config.get('top_k', 3)
        )
        
        generator = Generator(
            llm=llm,
            system_prompt=config.get('system_prompt')
        )
        
        pipeline = RAGPipeline(
            retriever=retriever,
            generator=generator,
            use_rag_threshold=config.get('rag_threshold', 0.5)
        )
        
        # Сохраняем в кэш
        self._pipelines[tenant_id] = pipeline
        
        print(f"{'='*60}")
        print(f"✅ RAG для '{tenant_id}' готов к работе")
        print(f"{'='*60}\n")
        
        return pipeline
    
    async def _initialize_llm(self, tenant_id: str, config: dict):
        """Инициализация LLM для клиента."""
        llm_type = config.get('llm_type', 'openrouter')
        
        print(f"🤖 Инициализация LLM (тип: {llm_type})...")
        
        if llm_type == 'openrouter':
            api_key = config.get('api_key') or os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                raise ValueError(f"OPENROUTER_API_KEY не найден для {tenant_id}")
            
            model = config.get('model', 'openai/gpt-4o-mini')
            print(f"   Модель: {model}")
            
            return OpenRouterLLM(
                model_name=model,
                api_key=api_key,
                temperature=config.get('temperature', 0.7),
                max_tokens=config.get('max_tokens', 1000),
                extra_headers={
                    "X-Title": f"qapsula_gpt2_{tenant_id}",
                    "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "")
                }
            )
        
        elif llm_type == 'openai':
            api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError(f"OPENAI_API_KEY не найден для {tenant_id}")
            
            model = config.get('model', 'gpt-4')
            print(f"   Модель: {model}")
            
            return OpenAILLM(
                model_name=model,
                api_key=api_key,
                temperature=config.get('temperature', 0.7),
                max_tokens=config.get('max_tokens', 1000)
            )
        
        elif llm_type == 'local':
            model_path = config.get('model_path')
            if not model_path:
                raise ValueError(f"model_path не указан для {tenant_id}")
            
            model_type = config.get('model_type', 'saiga')
            n_gpu_layers = config.get('n_gpu_layers', 0)
            
            print(f"   Модель: {model_path}")
            print(f"   Тип: {model_type}")
            print(f"   GPU layers: {n_gpu_layers}")
            
            if model_type == 'saiga':
                return SaigaLlamaCppLLM(
                    model_path=model_path,
                    n_gpu_layers=n_gpu_layers,
                    temperature=config.get('temperature', 0.7),
                    n_ctx=config.get('n_ctx', 4096)
                )
            elif model_type == 'mistral':
                return MistralLlamaCppLLM(
                    model_path=model_path,
                    n_gpu_layers=n_gpu_layers,
                    temperature=config.get('temperature', 0.7),
                    n_ctx=config.get('n_ctx', 4096)
                )
            else:
                return LlamaCppLLM(
                    model_path=model_path,
                    n_gpu_layers=n_gpu_layers,
                    temperature=config.get('temperature', 0.7),
                    n_ctx=config.get('n_ctx', 4096)
                )
        
        else:
            raise ValueError(f"Неизвестный тип LLM: {llm_type}")
    
    async def _initialize_vectorstore(
        self,
        tenant_id: str,
        documents_path: Path,
        vectorstore_path: Path
    ) -> FAISSVectorStore:
        """Инициализация векторного хранилища для клиента."""
        print(f"📊 Инициализация векторного хранилища...")
        
        vectorstore = FAISSVectorStore()
        
        # Проверяем существует ли уже хранилище
        index_path = vectorstore_path.with_suffix('.index')
        
        if index_path.exists():
            print(f"📂 Загрузка существующего хранилища...")
            await vectorstore.load(str(vectorstore_path))
            
            try:
                count = vectorstore.index.ntotal
                print(f"✓ Загружено {count} векторов")
            except Exception as e:
                print(f"⚠️  Не удалось получить количество векторов: {e}")
        
        else:
            print(f"🆕 Создание нового векторного хранилища...")
            
            # Проверяем есть ли документы для индексации
            if documents_path.exists():
                doc_files = list(documents_path.glob("*"))
                doc_files = [f for f in doc_files if f.suffix in ['.txt', '.md', '.pdf', '.docx']]
                
                if doc_files:
                    print(f"📄 Найдено документов: {len(doc_files)}")
                    
                    # Индексируем документы
                    ingestor = DocumentIngestor(vectorstore)
                    total_chunks = await ingestor.ingest_directory(
                        str(documents_path),
                        extensions=[".txt", ".md", ".pdf", ".docx"]
                    )
                    
                    print(f"✓ Проиндексировано {total_chunks} чанков")
                    
                    # Сохраняем хранилище
                    await vectorstore.save(str(vectorstore_path))
                    print(f"💾 Векторное хранилище сохранено")
                else:
                    print(f"⚠️  Документы не найдены в {documents_path}")
                    print(f"   Создано пустое хранилище")
            else:
                print(f"⚠️  Директория документов не существует")
                print(f"   Создано пустое хранилище")
        
        return vectorstore
    
    def _load_tenant_config(self, tenant_id: str) -> dict:
        """Загрузка конфигурации клиента из файла или переменных окружения."""
        # Пытаемся загрузить из YAML файла
        base_data_dir = Path(os.getenv("DATA_DIR", "./data"))
        config_path = base_data_dir / tenant_id / "config.yaml"
        
        if config_path.exists():
            print(f"📄 Загрузка конфигурации из {config_path}")
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"⚠️  Ошибка чтения конфига: {e}")
        
        # Конфигурация по умолчанию из .env
        print(f"📄 Использование конфигурации по умолчанию из .env")
        
        return {
            'llm_type': os.getenv('LLM_TYPE', 'openrouter'),
            'model': os.getenv('OPENROUTER_MODEL', 'openai/gpt-4o-mini'),
            'api_key': None,  # Будет взят из .env в _initialize_llm
            'temperature': float(os.getenv('TEMPERATURE', '0.7')),
            'max_tokens': int(os.getenv('MAX_TOKENS', '1000')),
            'top_k': int(os.getenv('RAG_TOP_K', '3')),
            'rag_threshold': float(os.getenv('USE_RAG_THRESHOLD', '0.5')),
            'system_prompt': None
        }
    
    def get_pipeline(self, tenant_id: str) -> Optional[RAGPipeline]:
        """Получить RAG pipeline для клиента."""
        return self._pipelines.get(tenant_id)
    
    def get_llm(self, tenant_id: str):
        """Получить LLM для клиента."""
        return self._llms.get(tenant_id)
    
    def get_vectorstore(self, tenant_id: str) -> Optional[FAISSVectorStore]:
        """Получить векторное хранилище для клиента."""
        return self._vectorstores.get(tenant_id)
    
    def list_tenants(self) -> list:
        """Список всех инициализированных клиентов."""
        return list(self._pipelines.keys())
    
    async def reload_tenant(self, tenant_id: str) -> RAGPipeline:
        """
        Перезагрузить RAG pipeline клиента.
        Полезно после обновления документов или конфигурации.
        """
        print(f"🔄 Перезагрузка RAG для '{tenant_id}'...")
        
        # Удаляем старые инстансы
        if tenant_id in self._pipelines:
            del self._pipelines[tenant_id]
        if tenant_id in self._llms:
            del self._llms[tenant_id]
        if tenant_id in self._vectorstores:
            del self._vectorstores[tenant_id]
        
        # Инициализируем заново
        return await self.initialize_tenant(tenant_id, force_reload=True)
    
    def get_stats(self) -> dict:
        """Получить общую статистику всех клиентов."""
        stats = {
            'total_tenants': len(self._pipelines),
            'tenants': {}
        }
        
        for tenant_id, pipeline in self._pipelines.items():
            try:
                vectorstore_size = pipeline.retriever.vectorstore.index.ntotal
            except:
                vectorstore_size = 0
            
            stats['tenants'][tenant_id] = {
                'vectorstore_size': vectorstore_size,
                'llm_type': type(self._llms.get(tenant_id)).__name__,
                'status': 'active'
            }
        
        return stats