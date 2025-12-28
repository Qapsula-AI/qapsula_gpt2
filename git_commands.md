# 📝 Git команды для проекта

## Первоначальная настройка

### 1. Инициализация репозитория

```bash
# Инициализация Git
git init

# Добавление всех файлов
git add .

# Первый коммит
git commit -m "Initial commit: Telegram RAG Bot setup"
```

### 2. Подключение к GitHub

```bash
# Создайте репозиторий на GitHub, затем:
git remote add origin https://github.com/your-username/telegram-rag-bot.git

# Или с SSH:
git remote add origin git@github.com:your-username/telegram-rag-bot.git

# Проверка
git remote -v

# Первый push
git branch -M main
git push -u origin main
```

## Структура файлов для коммита

```
telegram-rag-bot/
├── .gitignore
├── .env.example
├── README.md
├── QUICKSTART.md
├── DEPLOY.md
├── CHECKLIST.md
├── GIT_COMMANDS.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── setup.sh
├── deploy.sh
├── test_rag.py
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── telegram.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── openai.py
│   ├── vectorstore/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── faiss.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingest.py
│   │   ├── retriever.py
│   │   ├── generator.py
│   │   └── pipeline.py
│   └── schemas/
│       └── __init__.py
└── data/
    └── documents/
        └── sample_knowledge.txt
```

## Ежедневная работа

### Проверка статуса

```bash
git status
git log --oneline
```

### Добавление изменений

```bash
# Добавить все изменения
git add .

# Или выборочно
git add app/api/telegram.py
git add requirements.txt

# Коммит
git commit -m "feat: add RAG pipeline support"

# Push
git push origin main
```

### Полезные коммиты

```bash
# Новая функция
git commit -m "feat: add document ingestion"

# Исправление бага
git commit -m "fix: resolve OpenAI API timeout issue"

# Документация
git commit -m "docs: update README with deployment guide"

# Рефакторинг
git commit -m "refactor: improve RAG pipeline performance"

# Тесты
git commit -m "test: add unit tests for retriever"

# Стиль кода
git commit -m "style: format code with black"

# Обновление зависимостей
git commit -m "chore: update dependencies"
```

## Работа с ветками

### Создание feature branch

```bash
# Создать и переключиться на ветку
git checkout -b feature/add-streaming-support

# Работа в ветке
git add .
git commit -m "feat: add streaming response support"

# Push ветки
git push origin feature/add-streaming-support

# Переключение обратно на main
git checkout main

# Слияние
git merge feature/add-streaming-support

# Удаление ветки
git branch -d feature/add-streaming-support
git push origin --delete feature/add-streaming-support
```

## Обновление с удаленного репозитория

```bash
# Получить изменения
git fetch origin

# Слить изменения
git pull origin main

# Или в одну команду
git pull
```

## Откат изменений

### Отменить последний коммит (локально)

```bash
# Сохранить изменения
git reset --soft HEAD~1

# Удалить изменения
git reset --hard HEAD~1
```

### Отменить изменения в файле

```bash
git checkout -- app/main.py
```

### Откат коммита (создать новый коммит отмены)

```bash
git revert HEAD
```

## Игнорирование файлов

Убедитесь, что `.gitignore` содержит:

```
# Python
__pycache__/
*.pyc
venv/

# Environment
.env
.env.local

# Data
data/
*.index
*.docs

# IDE
.vscode/
.idea/
```

## Работа с тегами (релизы)

```bash
# Создать тег
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push тега
git push origin v1.0.0

# Или все теги
git push --tags

# Просмотр тегов
git tag

# Удаление тега
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```

## GitHub Actions (CI/CD)

Создайте `.github/workflows/main.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.10
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python -m pytest tests/
```

## Collaboration

### Fork workflow

```bash
# Fork репозиторий на GitHub

# Клонировать свой fork
git clone https://github.com/your-username/telegram-rag-bot.git

# Добавить upstream
git remote add upstream https://github.com/original-owner/telegram-rag-bot.git

# Синхронизация с upstream
git fetch upstream
git merge upstream/main
```

### Pull Request процесс

1. Создайте feature branch
```bash
git checkout -b feature/new-feature
```

2. Внесите изменения и коммит
```bash
git add .
git commit -m "feat: add new feature"
```

3. Push в свой fork
```bash
git push origin feature/new-feature
```

4. Создайте Pull Request на GitHub

## Полезные алиасы

Добавьте в `~/.gitconfig`:

```ini
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    lg = log --oneline --graph --decorate
    last = log -1 HEAD
    unstage = reset HEAD --
    undo = reset --soft HEAD~1
```

Использование:
```bash
git st
git co main
git lg
```

## Чистка истории

### Squash последних N коммитов

```bash
# Объединить последние 3 коммита
git rebase -i HEAD~3
```

В редакторе:
- Оставьте `pick` для первого коммита
- Измените `pick` на `squash` для остальных

## Stash (временное сохранение)

```bash
# Сохранить изменения
git stash

# Посмотреть список
git stash list

# Применить последние
git stash apply

# Применить конкретный
git stash apply stash@{1}

# Удалить последний
git stash drop
```

## Работа на сервере

### Обновление на production сервере

```bash
# SSH на сервер
ssh root@your-server-ip

# Перейти в директорию проекта
cd /opt/telegram-rag-bot

# Получить изменения
git pull origin main

# Перезапустить
docker-compose down
docker-compose up -d --build
```

### Автоматизация через webhook

Создайте скрипт `update.sh`:

```bash
#!/bin/bash
cd /opt/telegram-rag-bot
git pull origin main
docker-compose up -d --build
```

## Best Practices

1. **Коммитьте часто** - небольшие, атомарные изменения
2. **Пишите понятные сообщения** - описывайте что и зачем
3. **Используйте ветки** - для каждой фичи своя ветка
4. **Проверяйте перед push** - `git status`, `git diff`
5. **Не коммитьте секреты** - используйте `.gitignore`
6. **Синхронизируйтесь** - регулярно делайте `git pull`
7. **Делайте backup** - регулярно push в remote

## Troubleshooting

### Конфликты при pull

```bash
git pull origin main
# Если конфликты:
# Отредактируйте конфликтные файлы
git add .
git commit -m "resolve merge conflicts"
```

### Случайно закоммитили .env

```bash
# Удалить из Git, но оставить локально
git rm --cached .env
git commit -m "remove .env from git"
git push

# Обновить .gitignore
echo ".env" >> .gitignore
git add .gitignore
git commit -m "add .env to gitignore"
git push
```

### Большие файлы

```bash
# Если файл больше 100MB, используйте Git LFS
git lfs install
git lfs track "*.model"
git add .gitattributes
git commit -m "add Git LFS"
```
