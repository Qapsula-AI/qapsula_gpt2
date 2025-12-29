FROM python:3.11-slim

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    cmake \
    net-tools \          # для netstat
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
CMD ["python", "-m", "app.main_app"]