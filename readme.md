# Telegram Bot с GPT и RAG архитектурой

AI-powered Telegram бот с Retrieval-Augmented Generation (RAG) архитектурой для интеллектуальных ответов на основе загруженных документов.

## 🚀 Возможности

- 💬 Умный чат с GPT-4
- 📚 RAG система для работы с документами
- 🔍 Семантический поиск через FAISS
- 🧠 Контекстная память разговора
- 🌐 Поддержка русского языка
- 🐳 Docker поддержка

## 📁 Структура проекта

```
app/
├── api/
│   └── telegram.py          # Telegram бот
├── rag/
│   ├── ingest.py           # Загрузка документов
│   ├── retriever.py        # Поиск релевантных документов
│   ├── generator.py        # Генерация ответов
│   └── pipeline.py         # RAG pipeline
├── llm/
│   ├── base.py             # Базовый класс LLM
│   └── openai.py           # OpenAI интеграция
├── vectorstore/
│   ├── base.py             # Базовый класс хранилища
│   └── faiss.py            # FAISS векторное хранилище
├── schemas/
│   └── __init__.py         # Pydantic модели
└── main.py                  # Точка входа
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
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
VECTOR_STORE_PATH=./data/vectorstore
DOCUMENTS_PATH=./data/documents
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

### Изменение модели GPT

В `app/main.py`:

```python
llm = OpenAILLM(model_name="gpt-4-turbo-preview", temperature=0.7)
```

Доступные модели:
- `gpt-4-turbo-preview`
- `gpt-4`
- `gpt-3.5-turbo`

### Настройка RAG

В `app/main.py`:

```python
rag_pipeline = RAGPipeline(
    retriever=retriever,
    generator=generator,
    use_rag_threshold=0.5  # Минимальный порог релевантности (0-1)
)
```

### Параметры retriever

```python
retriever = Retriever(vectorstore, top_k=3)  # Количество документов
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
- [OpenAI API](https://platform.openai.com/docs)
- [FAISS](https://github.com/facebookresearch/faiss)
- [LangChain](https://python.langchain.com/)

## 🤝 Вклад

Pull requests приветствуются! Для больших изменений сначала откройте issue.

## 📄 Лицензия

MIT License
