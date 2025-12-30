#!/bin/bash

# Автоматическая загрузка глобальных настроек bash
if [ -f /etc/bash.bashrc ]; then
    source /etc/bash.bashrc
fi

# Переход в рабочую директорию проекта
if [ -d /opt/qapsula_gpt2 ]; then
    cd /opt/qapsula_gpt2
fi

# Приветственное сообщение
echo "✓ Загружены настройки из /etc/bash.bashrc"
echo "✓ Текущая директория: $(pwd)"
