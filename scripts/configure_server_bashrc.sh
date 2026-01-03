#!/bin/bash

# Скрипт для настройки автоматической загрузки окружения на сервере

echo "⚙️  Настройка автоматической загрузки окружения..."

# Добавляем команды в ~/.bashrc пользователя
BASHRC_CONTENT='
# Автоматическая загрузка глобальных настроек
if [ -f /etc/bash.bashrc ]; then
    source /etc/bash.bashrc
fi

# Переход в рабочую директорию проекта
if [ -d /opt/qapsula_gpt2 ]; then
    cd /opt/qapsula_gpt2
    echo "✓ Текущая директория: /opt/qapsula_gpt2"
fi
'

# Проверяем, не добавлены ли уже эти строки
if ! grep -q "cd /opt/qapsula_gpt2" ~/.bashrc; then
    echo "$BASHRC_CONTENT" >> ~/.bashrc
    echo "✓ Команды добавлены в ~/.bashrc"
else
    echo "✓ Команды уже присутствуют в ~/.bashrc"
fi

# Для root пользователя (если запускается от root)
if [ "$EUID" -eq 0 ]; then
    if ! grep -q "cd /opt/qapsula_gpt2" /root/.bashrc 2>/dev/null; then
        echo "$BASHRC_CONTENT" >> /root/.bashrc
        echo "✓ Команды добавлены в /root/.bashrc"
    fi
fi

echo ""
echo "✅ Настройка завершена!"
echo ""
echo "Теперь при входе на сервер автоматически будет:"
echo "  1. Загружаться /etc/bash.bashrc"
echo "  2. Выполняться переход в /opt/qapsula_gpt2"
echo ""
echo "Перезайдите в систему или выполните:"
echo "  source ~/.bashrc"
