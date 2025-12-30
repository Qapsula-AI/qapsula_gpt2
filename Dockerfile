FROM python:3.11-slim

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    cmake \
    net-tools \         
    && rm -rf /var/lib/apt/lists/*

# Создаем директорию проекта
RUN mkdir -p /opt/qapsula_gpt2

WORKDIR /opt/qapsula_gpt2

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Копируем .bashrc в домашнюю директорию root
COPY .bashrc /root/.bashrc

# Добавляем /opt/qapsula_gpt2 в PYTHONPATH
ENV PYTHONPATH=/opt/qapsula_gpt2

# Запускаем приложение через модуль Python
# main_app.py сам запустит FastAPI (uvicorn) и Telegram ботов
CMD ["python", "-u", "-m", "app.main_app"]