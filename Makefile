.PHONY: help install run test docker-build docker-up docker-down docker-logs clean

help:
	@echo "🤖 Telegram RAG Bot - Команды"
	@echo "install      - Установить зависимости"
	@echo "run          - Запустить бота"
	@echo "docker-up    - Запустить в Docker"
	@echo "docker-down  - Остановить Docker"
	@echo "docker-logs  - Показать логи"

install:
	pip install -r requirements.txt

run:
	python -m app.main

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f
