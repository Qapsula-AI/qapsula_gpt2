# Telegram Bot с GPT и RAG архитектурой

AI-powered Telegram бот и FastAPI сервис с Retrieval-Augmented Generation (RAG) архитектурой для интеллектуальных ответов на основе загруженных документов.

## 🚀 Быстрый старт

**[→ Запустить за 5 минут (QUICKSTART.md)](QUICKSTART.md)**

Полная инструкция по запуску проекта через Docker или локально.

## 💡 Возможности

- 💬 Умный чат с GPT-4 через OpenRouter или OpenAI
- 📚 RAG система для работы с документами
- 🔍 Семантический поиск через FAISS
- 🧠 Контекстная память разговора
- 🌐 Поддержка русского языка
- 🏢 Мультитенантность (разные клиенты с отдельными базами знаний)
- 🚀 FastAPI REST API + Telegram Bot
- 🐳 Docker поддержка

## 📁 Структура проекта

```
app/
├── api/
│   ├── telegram_bot.py     # Telegram бот
│   └── fastapi_app.py      # FastAPI REST API
├── core/
│   └── rag_manager.py      # Менеджер RAG инстансов (мультитенантность)
├── rag/
│   ├── rag_ingest.py       # Загрузка документов
│   ├── rag_retriever.py    # Поиск релевантных документов
│   ├── rag_generator.py    # Генерация ответов
│   └── rag_pipeline.py     # RAG pipeline
├── llm/
│   ├── llm_base.py         # Базовый класс LLM
│   ├── llm_openrouter.py   # OpenRouter интеграция
│   ├── llm_openai.py       # OpenAI интеграция (LangChain)
│   └── llm_llamacpp.py     # Локальные модели (закомментировано)
├── vectorstore/
│   ├── vectorstore_base.py # Базовый класс хранилища
│   └── vectorstore_faiss.py# FAISS векторное хранилище
├── schemas/
│   └── __init__.py         # Pydantic модели
└── main_app.py             # Точка входа
```

## 🛠 Установка

### 1. Клонируйте репозиторий

```bash
git clone <your-repo-url>
cd telegram-rag-bot
```

### 2. Создайте .env файл

```bash
cp .env.example .env
```

Заполните .env файл:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# LLM провайдер (openrouter или openai)
LLM_TYPE=openrouter

# OpenRouter (рекомендуется)
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_REFERER=https://your-site.com  # опционально

# OpenAI (альтернатива)
OPENAI_API_KEY=your_openai_api_key

# Настройки LLM
TEMPERATURE=0.7
MAX_TOKENS=1000

# RAG настройки
RAG_TOP_K=3
USE_RAG_THRESHOLD=0.5

# Пути к данным
DATA_DIR=./data
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Добавьте документы (опционально)

Поместите .txt или .md файлы в директорию `data/documents/`

## 🚀 Запуск

### Локально

```bash
python -m app.main
```

### С Docker

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## 📝 Использование

### Команды бота

- `/start` - Начать работу с ботом
- `/help` - Показать справку
- `/clear` - Очистить историю разговора

### Примеры

```
Пользователь: Привет!
Бот: Привет! 👋 Чем могу помочь?

Пользователь: Что такое машинное обучение?
Бот: [Ответ на основе загруженных документов или общих знаний]
```

## 🔧 Настройка

### Выбор LLM провайдера

Проект поддерживает два провайдера:

#### 1. OpenRouter (рекомендуется)
```env
LLM_TYPE=openrouter
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=openai/gpt-4o-mini
```

**Доступные модели:**
- `openai/gpt-4o-mini` (дешево, быстро)
- `openai/gpt-4o` (качественно)
- `anthropic/claude-3.5-sonnet`
- `google/gemini-pro`
- И [многие другие](https://openrouter.ai/models)

#### 2. OpenAI (прямое API)
```env
LLM_TYPE=openai
OPENAI_API_KEY=your_key
```

**Модели через config.yaml:**
```yaml
llm_type: openai
model: gpt-4-turbo-preview
temperature: 0.7
max_tokens: 1000
```

### Мультитенантность

Каждый клиент (tenant) имеет:
- Свою базу знаний (документы)
- Свой векторный индекс
- Свои настройки LLM

**Структура данных:**
```
data/
├── client1/
│   ├── config.yaml          # Настройки клиента
│   ├── documents/           # Документы клиента
│   └── vectorstore.index    # FAISS индекс
├── client2/
│   └── ...
└── default/                 # Клиент по умолчанию
    └── ...
```

**Пример config.yaml для клиента:**
```yaml
llm_type: openrouter
model: openai/gpt-4o-mini
temperature: 0.7
max_tokens: 1000
top_k: 3
rag_threshold: 0.5
system_prompt: "Ты специалист по техподдержке..."
```

### FastAPI эндпоинты

```bash
# Запуск сервера
uvicorn app.api.fastapi_app:app --host 127.0.0.1 --port 8000
```

**Основные эндпоинты:**
- `POST /api/chat` - Отправить сообщение
- `POST /api/upload` - Загрузить документ
- `GET /api/tenants` - Список клиентов
- `GET /api/health` - Статус сервера

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: client1" \
  -d '{
    "message": "Привет!",
    "chat_history": []
  }'
```

## 📊 Загрузка документов

### Программно

```python
from app.rag.ingest import DocumentIngestor
from app.vectorstore.faiss import FAISSVectorStore

vectorstore = FAISSVectorStore()
ingestor = DocumentIngestor(vectorstore)

# Загрузить один файл
await ingestor.ingest_file("path/to/document.txt")

# Загрузить директорию
await ingestor.ingest_directory("path/to/documents/", extensions=['.txt', '.md'])

# Загрузить текст напрямую
await ingestor.ingest_text("Ваш текст здесь", metadata={"source": "custom"})

# Сохранить векторное хранилище
await vectorstore.save("./data/vectorstore")
```

## 🧪 Тестирование

```bash
# Тест импортов
python -c "from app.main import main; print('OK')"

# Тест векторного хранилища
python -c "
import asyncio
from app.vectorstore.faiss import FAISSVectorStore
from app.rag.ingest import DocumentIngestor
from app.schemas import Document

async def test():
    vs = FAISSVectorStore()
    ing = DocumentIngestor(vs)
    await ing.ingest_text('Тестовый документ')
    results = await vs.similarity_search('тест', k=1)
    print(f'Найдено: {len(results)} документов')

asyncio.run(test())
"
```

## 🐛 Отладка

### Проверка логов

```bash
# Docker
docker-compose logs -f

# Локально
python -m app.main 2>&1 | tee bot.log
```

### Типичные проблемы

1. **Ошибка токена Telegram**
   - Проверьте `TELEGRAM_BOT_TOKEN` в .env
   - Получите новый токен у @BotFather

2. **Ошибка OpenAI API**
   - Проверьте `OPENAI_API_KEY` в .env
   - Убедитесь, что у вас есть средства на балансе

3. **Ошибки с зависимостями**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

## 📦 Деплой на Selectel

### 1. Подключитесь к серверу

```bash
ssh user@your-server-ip
```

### 2. Установите Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl start docker
sudo systemctl enable docker
```

### 3. Установите Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 4. Клонируйте репозиторий

```bash
git clone <your-repo-url>
cd telegram-rag-bot
```

### 5. Настройте .env

```bash
nano .env
# Вставьте ваши токены
```

### 6. Запустите бота

```bash
sudo docker-compose up -d
```

### 7. Проверьте статус

```bash
sudo docker-compose ps
sudo docker-compose logs -f
```

## 🔄 Обновление

```bash
git pull
sudo docker-compose down
sudo docker-compose up -d --build
```

## 📚 Дополнительная информация

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenRouter](https://openrouter.ai/) - Унифицированный доступ к LLM моделям
- [OpenAI API](https://platform.openai.com/docs)
- [FAISS](https://github.com/facebookresearch/faiss) - Векторный поиск от Facebook
- [LangChain](https://python.langchain.com/) - Фреймворк для LLM приложений
- [Sentence Transformers](https://www.sbert.net/) - Генерация эмбеддингов

## 🤝 Вклад

Pull requests приветствуются! Для больших изменений сначала откройте issue.

## 📄 Лицензия

MIT License
