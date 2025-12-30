.PHONY: help install run dev-up dev-down prod-up prod-down logs db-migrate db-upgrade db-downgrade clean

help:
	@echo "🤖 Qapsula RAG Bot - Команды"
	@echo ""
	@echo "Разработка:"
	@echo "  install        - Установить зависимости"
	@echo "  run            - Запустить локально"
	@echo "  dev-up         - Запустить dev окружение (Docker)"
	@echo "  dev-down       - Остановить dev окружение"
	@echo ""
	@echo "Production:"
	@echo "  prod-up        - Запустить production (Docker)"
	@echo "  prod-down      - Остановить production"
	@echo ""
	@echo "База данных:"
	@echo "  db-migrate     - Создать новую миграцию (Docker)"
	@echo "  db-upgrade     - Применить миграции (Docker)"
	@echo "  db-downgrade   - Откатить последнюю миграцию (Docker)"
	@echo ""
	@echo "Другое:"
	@echo "  logs           - Показать логи dev окружения"
	@echo "  logs-prod      - Показать логи production"
	@echo "  clean          - Очистить кэш и временные файлы"

install:
	pip install -r requirements.txt

run:
	python -m app.main_app

# Разработка (docker-compose.dev.yml)
dev-up:
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ Dev окружение запущено на http://127.0.0.1:8000"
	@echo "📊 PostgreSQL: localhost:5432 (postgres/postgres_dev_password)"

dev-down:
	docker-compose -f docker-compose.dev.yml down

# Production (docker-compose.yml)
prod-up:
	docker-compose up -d
	@echo "✅ Production запущен"

prod-down:
	docker-compose down

# Логи
logs:
	docker-compose -f docker-compose.dev.yml logs -f

logs-prod:
	docker-compose logs -f

# Миграции БД (через Docker)
db-migrate:
	docker-compose -f docker-compose.dev.yml exec app alembic revision --autogenerate -m "$(msg)"

db-upgrade:
	docker-compose -f docker-compose.dev.yml exec app alembic upgrade head

db-downgrade:
	docker-compose -f docker-compose.dev.yml exec app alembic downgrade -1

# Очистка
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} +
