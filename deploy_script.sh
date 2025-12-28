#!/bin/bash

# Скрипт для деплоя на Selectel или другой VPS

echo "🚀 Деплой Telegram RAG Bot"
echo "=========================="

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "📦 Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo systemctl start docker
    sudo systemctl enable docker
    rm get-docker.sh
    echo "✓ Docker установлен"
else
    echo "✓ Docker уже установлен: $(docker --version)"
fi

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Установка Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✓ Docker Compose установлен"
else
    echo "✓ Docker Compose уже установлен: $(docker-compose --version)"
fi

# Проверка .env файла
if [ ! -f .env ]; then
    echo "❌ .env файл не найден!"
    echo "📝 Создайте .env файл из .env.example:"
    echo "   cp .env.example .env"
    echo "   nano .env"
    exit 1
fi

echo "✓ .env файл найден"

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p data/vectorstore
mkdir -p data/documents

# Остановка старых контейнеров
echo "🛑 Остановка старых контейнеров..."
sudo docker-compose down

# Сборка и запуск
echo "🔨 Сборка и запуск контейнеров..."
sudo docker-compose up -d --build

# Проверка статуса
echo ""
echo "✅ Деплой завершен!"
echo ""
echo "📊 Статус контейнеров:"
sudo docker-compose ps

echo ""
echo "📋 Полезные команды:"
echo "  Логи:      sudo docker-compose logs -f"
echo "  Перезапуск: sudo docker-compose restart"
echo "  Остановка: sudo docker-compose down"
echo "  Обновление: git pull && sudo docker-compose up -d --build"
