FROM python:3.11-slim

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    cmake \
    net-tools \         
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Добавляем /app в PYTHONPATH
ENV PYTHONPATH=/app

# Запускаем приложение через модуль Python
# main_app.py сам запустит FastAPI (uvicorn) и Telegram ботов
CMD ["python", "-u", "-m", "app.main_app"]