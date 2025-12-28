FROM python:3.11-slim

WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# ВАЖНО: Добавляем /app в PYTHONPATH
ENV PYTHONPATH=/app

# Запускаем приложение
CMD ["python", "-m", "app.main_app"]