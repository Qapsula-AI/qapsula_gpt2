FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

RUN mkdir -p /app/data/vectorstore /app/data/documents

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "app.main_app"]
