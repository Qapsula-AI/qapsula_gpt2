# 🚀 Гайд по деплою на Selectel

Пошаговая инструкция для развертывания Telegram бота на сервере Selectel.

## Предварительные требования

- Сервер на Selectel (Ubuntu 20.04/22.04)
- SSH доступ к серверу
- Telegram Bot Token от @BotFather
- OpenAI API ключ

## Шаг 1: Подключение к серверу

```bash
ssh root@your-server-ip
```

## Шаг 2: Обновление системы

```bash
apt update && apt upgrade -y
```

## Шаг 3: Установка Git

```bash
apt install git -y
```

## Шаг 4: Клонирование репозитория

```bash
cd /opt
git clone https://github.com/your-username/telegram-rag-bot.git
cd telegram-rag-bot
```

## Шаг 5: Создание .env файла

```bash
cp .env.example .env
nano .env
```

Заполните файл:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
OPENAI_API_KEY=sk-...
VECTOR_STORE_PATH=./data/vectorstore
DOCUMENTS_PATH=./data/documents
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

## Шаг 6: Настройка окружения и запуск скрипта деплоя

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sed -i 's/\r$//' deploy_script.sh
chmod +x deploy_script.sh
./deploy_script.sh
```

Скрипт автоматически:
- Установит Docker и Docker Compose
- Создаст необходимые директории
- Соберет и запустит контейнеры

# Устанавливаем компиляторы и зависимости
apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gcc \
    g++ \
    python3-dev \
    libcurl4-openssl-dev

sudo docker-compose down
sudo docker-compose up -d --build

## Шаг 7: Проверка статуса

```bash
docker-compose ps
docker-compose logs -f
```

Должно быть видно:
```
telegram-rag-bot    Up    ...
```

## Шаг 8 (Опционально): Добавление документов

```bash
# Создайте директорию для документов, если её нет
mkdir -p data/documents

# Загрузите файлы через SCP с локальной машины
scp your-document.txt root@your-server-ip:/opt/telegram-rag-bot/data/documents/

# Или создайте файл напрямую на сервере
nano data/documents/knowledge.txt
```

После добавления документов перезапустите бота:

```bash
docker-compose restart
```

## Полезные команды

### Просмотр логов

```bash
docker-compose logs -f
```

### Перезапуск бота

```bash
docker-compose restart
```

### Остановка бота

```bash
docker-compose down
```

### Обновление кода

```bash
git pull
docker-compose up -d --build
```

### Очистка старых образов

```bash
docker system prune -a
```

## Настройка автозапуска

Создайте systemd сервис:

```bash
nano /etc/systemd/system/telegram-bot.service
```

Содержимое:

```ini
[Unit]
Description=Telegram RAG Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/telegram-rag-bot
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Активируйте сервис:

```bash
systemctl enable telegram-bot
systemctl start telegram-bot
systemctl status telegram-bot
```

## Мониторинг

### Проверка использования ресурсов

```bash
docker stats
```

### Проверка дискового пространства

```bash
df -h
du -sh data/
```

### Просмотр последних логов

```bash
docker-compose logs --tail=100
```

## Безопасность

### Настройка firewall

```bash
apt install ufw -y
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### Регулярные обновления

```bash
# Добавьте в crontab
crontab -e

# Добавьте строку для еженедельного обновления
0 3 * * 0 cd /opt/telegram-rag-bot && git pull && docker-compose up -d --build
```

## Troubleshooting

### Бот не запускается

1. Проверьте логи:
   ```bash
   docker-compose logs
   ```

2. Проверьте .env файл:
   ```bash
   cat .env
   ```

3. Проверьте, что порты не заняты:
   ```bash
   netstat -tulpn
   ```

### Ошибки с памятью

Если сервер имеет мало RAM, настройте swap:

```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### Проблемы с Docker

```bash
# Перезапуск Docker
systemctl restart docker

# Проверка статуса
systemctl status docker

# Просмотр логов Docker
journalctl -u docker -f
```

## Бэкапы

### Backup векторного хранилища

```bash
tar -czf backup-$(date +%Y%m%d).tar.gz data/
scp backup-*.tar.gz user@backup-server:/backups/
```

### Автоматический backup (cron)

```bash
crontab -e

# Добавьте ежедневный бэкап в 2 часа ночи
0 2 * * * cd /opt/telegram-rag-bot && tar -czf /backups/backup-$(date +\%Y\%m\%d).tar.gz data/
```

## Обновление зависимостей

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Полезные ссылки

- [Selectel VPS](https://selectel.ru/services/cloud/servers/)
- [Docker документация](https://docs.docker.com/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenAI API](https://platform.openai.com/docs)

## Поддержка

Если возникли проблемы:
1. Проверьте логи: `docker-compose logs -f`
2. Проверьте статус: `docker-compose ps`
3. Создайте issue на GitHub
